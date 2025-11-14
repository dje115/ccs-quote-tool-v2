#!/usr/bin/env python3
"""
WebSocket Manager for Real-Time Updates
Manages WebSocket connections and broadcasts events from Redis Pub/Sub
"""

import json
import asyncio
import redis.asyncio as redis
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.core.config import settings


class WebSocketManager:
    """
    Manages WebSocket connections with tenant isolation
    Connections are grouped by tenant_id for multi-tenant security
    """
    
    def __init__(self):
        # tenant_id -> {user_id -> [websocket_connections]}
        self.active_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}
        self.redis_subscriber: Optional[redis.Redis] = None
        self.redis_pubsub: Optional[redis.client.PubSub] = None
        self.subscribed_tenants: Set[str] = set()
        self._running = False
    
    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        """
        Connect a WebSocket client
        
        Args:
            websocket: WebSocket connection
            tenant_id: Tenant ID for isolation
            user_id: User ID for tracking
        """
        await websocket.accept()
        
        # Initialize tenant/user structure if needed
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = {}
        if user_id not in self.active_connections[tenant_id]:
            self.active_connections[tenant_id][user_id] = set()
        
        # Add connection
        self.active_connections[tenant_id][user_id].add(websocket)
        
        # Subscribe to tenant's Redis channel if not already subscribed
        if tenant_id not in self.subscribed_tenants:
            await self._subscribe_to_tenant(tenant_id)
        
        print(f"✅ WebSocket connected: tenant={tenant_id}, user={user_id}, total_connections={self._count_connections()}")
    
    def disconnect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        """
        Disconnect a WebSocket client
        
        Args:
            websocket: WebSocket connection
            tenant_id: Tenant ID
            user_id: User ID
        """
        if tenant_id in self.active_connections:
            if user_id in self.active_connections[tenant_id]:
                self.active_connections[tenant_id][user_id].discard(websocket)
                
                # Clean up empty sets
                if not self.active_connections[tenant_id][user_id]:
                    del self.active_connections[tenant_id][user_id]
            
            # Clean up empty tenant dicts
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
                self.subscribed_tenants.discard(tenant_id)
        
        print(f"❌ WebSocket disconnected: tenant={tenant_id}, user={user_id}, total_connections={self._count_connections()}")
    
    async def _subscribe_to_tenant(self, tenant_id: str):
        """Subscribe to Redis Pub/Sub channel for a tenant"""
        if not self.redis_subscriber:
            await self._init_redis()
        
        if self.redis_subscriber and tenant_id not in self.subscribed_tenants:
            channel = f"tenant:{tenant_id}:events"
            try:
                await self.redis_pubsub.subscribe(channel)
                self.subscribed_tenants.add(tenant_id)
                print(f"📡 Subscribed to Redis channel: {channel}")
            except Exception as e:
                print(f"❌ WebSocketManager: Failed to subscribe to {channel}: {e}")
    
    async def _init_redis(self):
        """Initialize Redis connection for Pub/Sub"""
        try:
            self.redis_subscriber = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            self.redis_pubsub = self.redis_subscriber.pubsub()
            
            # Start listening for messages
            if not self._running:
                self._running = True
                asyncio.create_task(self._listen_to_redis())
            
            print("✅ WebSocketManager: Redis Pub/Sub initialized")
        except Exception as e:
            print(f"❌ WebSocketManager: Redis initialization failed: {e}")
            self.redis_subscriber = None
            self.redis_pubsub = None
    
    async def _listen_to_redis(self):
        """Listen to Redis Pub/Sub messages and broadcast to WebSocket clients"""
        while self._running:
            try:
                if not self.redis_pubsub:
                    await asyncio.sleep(1)
                    continue
                
                try:
                    message = await asyncio.wait_for(
                        self.redis_pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                if message and message.get('type') == 'message':
                    await self._handle_redis_message(message)
            except Exception as e:
                print(f"❌ WebSocketManager: Error listening to Redis: {e}")
                await asyncio.sleep(1)
    
    async def _handle_redis_message(self, message: dict):
        """Handle incoming Redis Pub/Sub message"""
        try:
            channel = message['channel']
            data = json.loads(message['data'])
            
            # Extract tenant_id from channel name (tenant:{tenant_id}:events)
            tenant_id = channel.replace('tenant:', '').replace(':events', '')
            
            # Validate tenant_id matches event tenant_id
            if data.get('tenant_id') != tenant_id:
                print(f"⚠️ WebSocketManager: Tenant ID mismatch: channel={tenant_id}, event={data.get('tenant_id')}")
                return
            
            # Broadcast to all connections for this tenant
            await self._broadcast_to_tenant(tenant_id, data)
        except Exception as e:
            print(f"❌ WebSocketManager: Error handling Redis message: {e}")
    
    async def _broadcast_to_tenant(self, tenant_id: str, event: dict):
        """Broadcast event to all WebSocket connections for a tenant"""
        if tenant_id not in self.active_connections:
            return
        
        # Collect all connections for this tenant
        connections_to_remove = []
        
        for user_id, connections in self.active_connections[tenant_id].items():
            for connection in connections:
                try:
                    await connection.send_json(event)
                except Exception as e:
                    print(f"⚠️ WebSocketManager: Error sending to connection: {e}")
                    connections_to_remove.append((tenant_id, user_id, connection))
        
        # Remove dead connections
        for tenant_id, user_id, connection in connections_to_remove:
            self.disconnect(connection, tenant_id, user_id)
    
    def _count_connections(self) -> int:
        """Count total active connections"""
        total = 0
        for tenant_connections in self.active_connections.values():
            for user_connections in tenant_connections.values():
                total += len(user_connections)
        return total
    
    async def close(self):
        """Close all connections and cleanup"""
        self._running = False
        if self.redis_pubsub:
            await self.redis_pubsub.unsubscribe()
        if self.redis_subscriber:
            await self.redis_subscriber.close()
        print("🛑 WebSocketManager: Closed all connections")


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get global WebSocket manager instance"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager

