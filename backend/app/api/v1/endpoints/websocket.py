#!/usr/bin/env python3
"""
WebSocket endpoint for real-time updates
Provides tenant-isolated WebSocket connections for instant updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from jose import jwt
from app.core.config import settings
from app.core.websocket import get_websocket_manager
from app.core.database import SessionLocal
from app.models.tenant import User

router = APIRouter()


async def authenticate_websocket(websocket: WebSocket, token: str) -> tuple[str, str]:
    """
    Authenticate WebSocket connection using JWT token
    
    Returns:
        tuple: (tenant_id, user_id)
    
    Raises:
        HTTPException: If authentication fails
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Return tenant_id and user_id
        return (user.tenant_id, user_id)
    
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    finally:
        db.close()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time updates
    
    Query Parameters:
        token: JWT authentication token
    
    The WebSocket connection is tenant-scoped - users only receive
    events for their tenant. All events are published to Redis Pub/Sub
    and broadcast to connected clients.
    """
    tenant_id = None
    user_id = None
    
    try:
        # Authenticate connection
        tenant_id, user_id = await authenticate_websocket(websocket, token)
        
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
    
    except HTTPException as e:
        # Send error and close connection
        try:
            await websocket.send_json({
                "type": "error",
                "message": e.detail
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
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

