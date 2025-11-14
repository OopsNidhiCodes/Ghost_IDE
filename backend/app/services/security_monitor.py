"""
Security monitoring service for GhostIDE
Monitors security events, detects suspicious patterns, and triggers alerts
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: str
    client_ip: str
    timestamp: datetime
    details: Dict
    threat_level: ThreatLevel = ThreatLevel.LOW
    session_id: Optional[str] = None


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_type: str
    threat_level: ThreatLevel
    client_ip: str
    timestamp: datetime
    description: str
    events: List[SecurityEvent]
    recommended_action: str


class SecurityMonitor:
    """Main security monitoring service"""
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.ip_events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.blocked_ips: Set[str] = set()
        self.alerts: deque = deque(maxlen=1000)  # Keep last 1k alerts
        
        # Threat detection thresholds
        self.thresholds = {
            'failed_validations_per_minute': 5,
            'rate_limit_violations_per_hour': 3,
            'suspicious_patterns_per_hour': 10,
            'different_sessions_per_ip': 20,
            'code_execution_failures_per_minute': 8
        }
        
        # Pattern detection
        self.suspicious_patterns = [
            'multiple_session_mismatch',
            'rapid_language_switching',
            'repeated_dangerous_code',
            'unusual_execution_patterns',
            'high_frequency_ai_requests'
        ]
    
    def log_event(self, event: SecurityEvent):
        """Log a security event"""
        self.events.append(event)
        self.ip_events[event.client_ip].append(event)
        
        # Analyze event for threats
        self._analyze_event(event)
        
        logger.info(f"Security event logged: {event.event_type} from {event.client_ip}")
    
    def _analyze_event(self, event: SecurityEvent):
        """Analyze event for potential threats"""
        client_ip = event.client_ip
        
        # Check for rapid-fire events
        if self._check_rapid_events(client_ip, event.event_type):
            self._create_alert(
                'RAPID_EVENTS',
                ThreatLevel.MEDIUM,
                client_ip,
                f"Rapid {event.event_type} events detected",
                [event],
                "Monitor client activity, consider temporary rate limiting"
            )
        
        # Check for validation failures
        if event.event_type == 'INPUT_VALIDATION_FAILURE':
            if self._check_validation_failures(client_ip):
                self._create_alert(
                    'MULTIPLE_VALIDATION_FAILURES',
                    ThreatLevel.HIGH,
                    client_ip,
                    "Multiple input validation failures detected",
                    self._get_recent_events(client_ip, 'INPUT_VALIDATION_FAILURE', minutes=5),
                    "Block IP temporarily, investigate for attack patterns"
                )
        
        # Check for session anomalies
        if 'SESSION_MISMATCH' in event.event_type:
            if self._check_session_anomalies(client_ip):
                self._create_alert(
                    'SESSION_ANOMALIES',
                    ThreatLevel.HIGH,
                    client_ip,
                    "Multiple session mismatches detected",
                    self._get_recent_events(client_ip, 'SESSION_MISMATCH', minutes=10),
                    "Investigate for session hijacking attempts, consider blocking IP"
                )
        
        # Check for code execution abuse
        if event.event_type == 'CODE_EXECUTION_REQUEST':
            if self._check_execution_abuse(client_ip):
                self._create_alert(
                    'CODE_EXECUTION_ABUSE',
                    ThreatLevel.MEDIUM,
                    client_ip,
                    "Excessive code execution requests detected",
                    self._get_recent_events(client_ip, 'CODE_EXECUTION_REQUEST', minutes=5),
                    "Apply stricter rate limiting for code execution"
                )
    
    def _check_rapid_events(self, client_ip: str, event_type: str, window_minutes: int = 1) -> bool:
        """Check for rapid-fire events from same IP"""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_events = [
            e for e in self.ip_events[client_ip] 
            if e.timestamp > cutoff and e.event_type == event_type
        ]
        
        # Different thresholds for different event types
        thresholds = {
            'CODE_EXECUTION_REQUEST': 15,
            'AI_CHAT_REQUEST': 30,
            'INPUT_VALIDATION_FAILURE': 5,
            'RATE_LIMIT_VIOLATION': 1
        }
        
        threshold = thresholds.get(event_type, 10)
        return len(recent_events) > threshold
    
    def _check_validation_failures(self, client_ip: str) -> bool:
        """Check for multiple validation failures"""
        cutoff = datetime.now() - timedelta(minutes=5)
        failures = [
            e for e in self.ip_events[client_ip]
            if e.timestamp > cutoff and e.event_type == 'INPUT_VALIDATION_FAILURE'
        ]
        return len(failures) >= self.thresholds['failed_validations_per_minute']
    
    def _check_session_anomalies(self, client_ip: str) -> bool:
        """Check for session-related anomalies"""
        cutoff = datetime.now() - timedelta(minutes=10)
        session_events = [
            e for e in self.ip_events[client_ip]
            if e.timestamp > cutoff and 'SESSION' in e.event_type
        ]
        
        # Check for multiple different sessions from same IP
        sessions = set()
        mismatches = 0
        
        for event in session_events:
            if event.session_id:
                sessions.add(event.session_id)
            if 'MISMATCH' in event.event_type:
                mismatches += 1
        
        return (len(sessions) > self.thresholds['different_sessions_per_ip'] or 
                mismatches >= 3)
    
    def _check_execution_abuse(self, client_ip: str) -> bool:
        """Check for code execution abuse patterns"""
        cutoff = datetime.now() - timedelta(minutes=5)
        executions = [
            e for e in self.ip_events[client_ip]
            if e.timestamp > cutoff and e.event_type == 'CODE_EXECUTION_REQUEST'
        ]
        
        return len(executions) > self.thresholds['code_execution_failures_per_minute']
    
    def _get_recent_events(self, client_ip: str, event_type: str, minutes: int = 5) -> List[SecurityEvent]:
        """Get recent events of specific type for IP"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            e for e in self.ip_events[client_ip]
            if e.timestamp > cutoff and event_type in e.event_type
        ]
    
    def _create_alert(self, alert_type: str, threat_level: ThreatLevel, 
                     client_ip: str, description: str, events: List[SecurityEvent],
                     recommended_action: str):
        """Create and log security alert"""
        alert = SecurityAlert(
            alert_type=alert_type,
            threat_level=threat_level,
            client_ip=client_ip,
            timestamp=datetime.now(),
            description=description,
            events=events,
            recommended_action=recommended_action
        )
        
        self.alerts.append(alert)
        
        # Log alert based on threat level
        if threat_level == ThreatLevel.CRITICAL:
            logger.critical(f"SECURITY ALERT: {description} from {client_ip}")
        elif threat_level == ThreatLevel.HIGH:
            logger.error(f"SECURITY ALERT: {description} from {client_ip}")
        elif threat_level == ThreatLevel.MEDIUM:
            logger.warning(f"SECURITY ALERT: {description} from {client_ip}")
        else:
            logger.info(f"SECURITY ALERT: {description} from {client_ip}")
        
        # Auto-block for critical threats
        if threat_level == ThreatLevel.CRITICAL:
            self.block_ip(client_ip, f"Auto-blocked due to {alert_type}")
    
    def block_ip(self, client_ip: str, reason: str):
        """Block an IP address"""
        self.blocked_ips.add(client_ip)
        logger.warning(f"IP {client_ip} blocked: {reason}")
        
        # Create blocking event
        block_event = SecurityEvent(
            event_type='IP_BLOCKED',
            client_ip=client_ip,
            timestamp=datetime.now(),
            details={'reason': reason},
            threat_level=ThreatLevel.HIGH
        )
        self.log_event(block_event)
    
    def unblock_ip(self, client_ip: str):
        """Unblock an IP address"""
        if client_ip in self.blocked_ips:
            self.blocked_ips.remove(client_ip)
            logger.info(f"IP {client_ip} unblocked")
    
    def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked"""
        return client_ip in self.blocked_ips
    
    def get_ip_threat_score(self, client_ip: str) -> float:
        """Calculate threat score for IP (0-100)"""
        if client_ip in self.blocked_ips:
            return 100.0
        
        score = 0.0
        cutoff = datetime.now() - timedelta(hours=1)
        
        recent_events = [
            e for e in self.ip_events[client_ip]
            if e.timestamp > cutoff
        ]
        
        # Score based on event types and frequency
        for event in recent_events:
            if event.event_type == 'INPUT_VALIDATION_FAILURE':
                score += 10
            elif 'SESSION_MISMATCH' in event.event_type:
                score += 15
            elif event.event_type == 'RATE_LIMIT_VIOLATION':
                score += 5
            elif event.event_type == 'SUSPICIOUS_ACTIVITY':
                score += 20
        
        # Bonus for rapid events
        if len(recent_events) > 50:
            score += 25
        
        return min(score, 100.0)
    
    def get_security_summary(self) -> Dict:
        """Get security monitoring summary"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        recent_events = [e for e in self.events if e.timestamp > last_hour]
        daily_events = [e for e in self.events if e.timestamp > last_day]
        recent_alerts = [a for a in self.alerts if a.timestamp > last_hour]
        
        return {
            'total_events_last_hour': len(recent_events),
            'total_events_last_day': len(daily_events),
            'alerts_last_hour': len(recent_alerts),
            'blocked_ips': len(self.blocked_ips),
            'high_threat_ips': len([
                ip for ip in self.ip_events.keys() 
                if self.get_ip_threat_score(ip) > 70
            ]),
            'event_types_last_hour': {
                event_type: len([e for e in recent_events if e.event_type == event_type])
                for event_type in set(e.event_type for e in recent_events)
            },
            'top_threat_ips': sorted([
                {'ip': ip, 'score': self.get_ip_threat_score(ip)}
                for ip in list(self.ip_events.keys())[-20:]  # Last 20 IPs
            ], key=lambda x: x['score'], reverse=True)[:5]
        }
    
    def cleanup_old_events(self):
        """Clean up old events and alerts"""
        cutoff = datetime.now() - timedelta(days=7)
        
        # Clean up old events from IP tracking
        for ip in list(self.ip_events.keys()):
            old_events = deque()
            for event in self.ip_events[ip]:
                if event.timestamp > cutoff:
                    old_events.append(event)
            self.ip_events[ip] = old_events
            
            # Remove empty IP entries
            if not self.ip_events[ip]:
                del self.ip_events[ip]
        
        logger.info("Cleaned up old security events")


# Global security monitor instance
security_monitor = SecurityMonitor()


async def start_security_monitoring():
    """Start security monitoring background tasks"""
    async def cleanup_task():
        while True:
            await asyncio.sleep(3600)  # Run every hour
            security_monitor.cleanup_old_events()
    
    asyncio.create_task(cleanup_task())
    logger.info("Security monitoring started")


def log_security_event(event_type: str, client_ip: str, details: Dict, 
                      threat_level: ThreatLevel = ThreatLevel.LOW,
                      session_id: Optional[str] = None):
    """Convenience function to log security events"""
    event = SecurityEvent(
        event_type=event_type,
        client_ip=client_ip,
        timestamp=datetime.now(),
        details=details,
        threat_level=threat_level,
        session_id=session_id
    )
    security_monitor.log_event(event)