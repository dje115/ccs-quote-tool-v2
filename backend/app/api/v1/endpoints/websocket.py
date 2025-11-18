#!/usr/bin/env python3
"""
WebSocket endpoint for real-time updates
Provides tenant-isolated WebSocket connections for instant updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status, Cookie
from jose import jwt
import json
from typing import Optional
from app.core.config import settings
from app.core.websocket import get_websocket_manager
from app.core.database import SessionLocal
from app.models.tenant import User

router = APIRouter()


async def authenticate_websocket(websocket: WebSocket, token: Optional[str] = None) -> tuple[str, str]:
    """
    Authenticate WebSocket connection using JWT token
    
    Returns:
        tuple: (tenant_id, user_id)
    
    Raises:
        Exception: If authentication fails (will be caught and connection closed)
    """
    db = SessionLocal()
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token: missing user ID")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError("User not found")
        
        if not user.is_active:
            raise ValueError("Inactive user")
        
        # Return tenant_id and user_id
        return (user.tenant_id, user_id)
    
    except jwt.JWTError:
        raise ValueError("Invalid token: JWT decode error")
    finally:
        db.close()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token")
):
    """
    WebSocket endpoint for real-time updates
    
    SECURITY: Token can be provided via:
    1. HttpOnly cookie (preferred) - sent automatically in WebSocket handshake
    2. First message after connection (fallback) - Format: {"type": "auth", "token": "..."}
    
    Query parameters are NOT supported to prevent token leakage in logs/caches.
    
    The WebSocket connection is tenant-scoped - users only receive
    events for their tenant. All events are published to Redis Pub/Sub
    and broadcast to connected clients.
    """
    tenant_id = None
    user_id = None
    token = None
    
    try:
        # Accept connection first
        await websocket.accept()
        
        # SECURITY: Try to get token from HttpOnly cookie first (preferred method)
        # WebSocket handshake is an HTTP request, so cookies are available
        token = access_token_cookie
        
        # If no cookie, try to get token from first message (fallback for clients without cookies)
        if not token:
            try:
                # Set timeout for auth message (5 seconds)
                import asyncio
                auth_data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                auth_message = json.loads(auth_data)
                
                if auth_message.get("type") != "auth":
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="First message must be auth message")
                    return
                
                token = auth_message.get("token")
                if not token:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token in auth message or cookie")
                    return
                    
            except asyncio.TimeoutError:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication timeout")
                return
            except json.JSONDecodeError:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="Invalid auth message format")
                return
        
        # Authenticate connection
        try:
            tenant_id, user_id = await authenticate_websocket(websocket, token)
        except ValueError as e:
            # Authentication failed - close connection with appropriate code
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
            return
        
        # Connect to WebSocket manager
        manager = get_websocket_manager()
        await manager.connect(websocket, tenant_id, user_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection.established",
            "tenant_id": tenant_id,
            "user_id": user_id,
            "message": "WebSocket connected successfully"
        })
        
        # Keep connection alive and handle incoming messages
        try:
            while True:
                try:
                    # Wait for messages (ping/pong for keepalive)
                    # Use receive_text() for text messages
                    data = await websocket.receive_text()
                    
                    # Handle ping messages
                    if data == "ping":
                        await websocket.send_text("pong")
                except WebSocketDisconnect:
                    # Normal disconnect
                    break
                except Exception as e:
                    # Log the actual error
                    import traceback
                    print(f"❌ WebSocket receive error: {e}")
                    print(traceback.format_exc())
                    # Check if connection is still open
                    if websocket.client_state.name == "DISCONNECTED":
                        break
                    # Otherwise, continue listening
                    continue
        except WebSocketDisconnect:
            # Outer catch for disconnect
            pass
    
    except ValueError as e:
        # Authentication error - already handled above, but catch here for safety
        try:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
        except:
            pass
    
    except Exception as e:
        import traceback
        print(f"❌ WebSocket error: {e}")
        print(traceback.format_exc())
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
            await websocket.close()
        except:
            pass
    
    finally:
        # Disconnect from manager
        if tenant_id and user_id:
            manager = get_websocket_manager()
            manager.disconnect(websocket, tenant_id, user_id)

