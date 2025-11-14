"""
Security monitoring and management API endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.middleware.auth import require_valid_session
from app.services.security_monitor import security_monitor, ThreatLevel
from app.middleware.security import security_logger

logger = logging.getLogger(__name__)

router = APIRouter()


class SecuritySummaryResponse(BaseModel):
    """Security summary response model"""
    total_events_last_hour: int
    total_events_last_day: int
    alerts_last_hour: int
    blocked_ips: int
    high_threat_ips: int
    event_types_last_hour: Dict[str, int]
    top_threat_ips: List[Dict[str, Any]]


class IPThreatResponse(BaseModel):
    """IP threat score response model"""
    ip_address: str
    threat_score: float
    is_blocked: bool
    recent_events: int
    last_activity: str


@router.get("/summary", response_model=SecuritySummaryResponse)
async def get_security_summary(
    request: Request,
    session: Dict = Depends(require_valid_session)
):
    """
    Get security monitoring summary
    Requires valid session authentication.
    """
    try:
        # Log access to security dashboard
        client_ip = request.headers.get('X-Forwarded-For', request.client.host if request.client else 'unknown')
        security_logger.log_security_event(
            'SECURITY_DASHBOARD_ACCESS',
            client_ip,
            {'session_id': session['session_id']}
        )
        
        summary = security_monitor.get_security_summary()
        return SecuritySummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting security summary: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve security summary"
        )


@router.get("/ip/{ip_address}", response_model=IPThreatResponse)
async def get_ip_threat_info(
    ip_address: str,
    request: Request,
    session: Dict = Depends(require_valid_session)
):
    """
    Get threat information for specific IP address
    """
    try:
        # Validate IP format (basic check)
        if not ip_address.replace('.', '').replace(':', '').isalnum():
            raise HTTPException(
                status_code=400,
                detail="Invalid IP address format"
            )
        
        # Log IP lookup
        client_ip = request.headers.get('X-Forwarded-For', request.client.host if request.client else 'unknown')
        security_logger.log_security_event(
            'IP_THREAT_LOOKUP',
            client_ip,
            {'target_ip': ip_address, 'session_id': session['session_id']}
        )
        
        threat_score = security_monitor.get_ip_threat_score(ip_address)
        is_blocked = security_monitor.is_ip_blocked(ip_address)
        
        # Get recent events count
        cutoff = datetime.now() - timedelta(hours=1)
        recent_events = len([
            e for e in security_monitor.ip_events.get(ip_address, [])
            if e.timestamp > cutoff
        ])
        
        # Get last activity
        last_activity = "Never"
        if ip_address in security_monitor.ip_events and security_monitor.ip_events[ip_address]:
            last_event = max(security_monitor.ip_events[ip_address], key=lambda x: x.timestamp)
            last_activity = last_event.timestamp.isoformat()
        
        return IPThreatResponse(
            ip_address=ip_address,
            threat_score=threat_score,
            is_blocked=is_blocked,
            recent_events=recent_events,
            last_activity=last_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting IP threat info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve IP threat information"
        )


@router.post("/block-ip/{ip_address}")
async def block_ip_address(
    ip_address: str,
    request: Request,
    session: Dict = Depends(require_valid_session)
):
    """
    Block an IP address manually
    """
    try:
        # Validate IP format
        if not ip_address.replace('.', '').replace(':', '').isalnum():
            raise HTTPException(
                status_code=400,
                detail="Invalid IP address format"
            )
        
        # Don't allow blocking own IP
        client_ip = request.headers.get('X-Forwarded-For', request.client.host if request.client else 'unknown')
        if ip_address == client_ip:
            raise HTTPException(
                status_code=400,
                detail="Cannot block your own IP address"
            )
        
        # Log manual block action
        security_logger.log_security_event(
            'MANUAL_IP_BLOCK',
            client_ip,
            {'blocked_ip': ip_address, 'session_id': session['session_id']}
        )
        
        security_monitor.block_ip(ip_address, f"Manually blocked by session {session['session_id']}")
        
        return {
            "message": f"IP {ip_address} has been blocked",
            "blocked_by": session['session_id'],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to block IP address"
        )


@router.post("/unblock-ip/{ip_address}")
async def unblock_ip_address(
    ip_address: str,
    request: Request,
    session: Dict = Depends(require_valid_session)
):
    """
    Unblock an IP address manually
    """
    try:
        # Validate IP format
        if not ip_address.replace('.', '').replace(':', '').isalnum():
            raise HTTPException(
                status_code=400,
                detail="Invalid IP address format"
            )
        
        # Log manual unblock action
        client_ip = request.headers.get('X-Forwarded-For', request.client.host if request.client else 'unknown')
        security_logger.log_security_event(
            'MANUAL_IP_UNBLOCK',
            client_ip,
            {'unblocked_ip': ip_address, 'session_id': session['session_id']}
        )
        
        security_monitor.unblock_ip(ip_address)
        
        return {
            "message": f"IP {ip_address} has been unblocked",
            "unblocked_by": session['session_id'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to unblock IP address"
        )


@router.get("/alerts")
async def get_recent_alerts(
    request: Request,
    session: Dict = Depends(require_valid_session),
    limit: int = 50
):
    """
    Get recent security alerts
    """
    try:
        # Log alerts access
        client_ip = request.headers.get('X-Forwarded-For', request.client.host if request.client else 'unknown')
        security_logger.log_security_event(
            'SECURITY_ALERTS_ACCESS',
            client_ip,
            {'session_id': session['session_id'], 'limit': limit}
        )
        
        # Get recent alerts
        recent_alerts = list(security_monitor.alerts)[-limit:]
        
        # Convert to serializable format
        alerts_data = []
        for alert in recent_alerts:
            alerts_data.append({
                'alert_type': alert.alert_type,
                'threat_level': alert.threat_level.value,
                'client_ip': alert.client_ip,
                'timestamp': alert.timestamp.isoformat(),
                'description': alert.description,
                'recommended_action': alert.recommended_action,
                'event_count': len(alert.events)
            })
        
        return {
            "alerts": alerts_data,
            "total_count": len(alerts_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting security alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve security alerts"
        )


@router.get("/health")
async def security_health_check():
    """
    Security system health check
    """
    try:
        # Basic health metrics
        total_events = len(security_monitor.events)
        total_ips = len(security_monitor.ip_events)
        blocked_ips = len(security_monitor.blocked_ips)
        
        # Check if monitoring is working
        recent_events = len([
            e for e in security_monitor.events
            if e.timestamp > datetime.now() - timedelta(minutes=5)
        ])
        
        status = "healthy"
        if total_events == 0:
            status = "no_events"
        elif recent_events == 0:
            status = "no_recent_activity"
        
        return {
            "status": status,
            "total_events": total_events,
            "total_ips_tracked": total_ips,
            "blocked_ips": blocked_ips,
            "recent_events_5min": recent_events,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }