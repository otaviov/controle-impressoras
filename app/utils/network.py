from __future__ import annotations

import logging
import subprocess
import sys
import time
from typing import Optional

log = logging.getLogger(__name__)


def ping(host: str, timeout_ms: int = 2000, retries: int = 1) -> Optional[float]:
    if not host or host == "0.0.0.0":
        return None
    for _ in range(retries):
        try:
            if sys.platform == "win32":
                args = ["ping", "-n", "1", "-w", str(timeout_ms), host]
            else:
                args = ["ping", "-c", "1", "-W", str(timeout_ms // 1000), host]
            start = time.monotonic()
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=max(timeout_ms // 1000 + 1, 3),
            )
            elapsed = (time.monotonic() - start) * 1000
            if proc.returncode == 0:
                return round(elapsed, 1)
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            log.debug("ping %s falhou: %s", host, e)
    return None


def snmp_get(host: str, oid: str, community: str = "public", port: int = 161, timeout: int = 3) -> Optional[str]:
    try:
        from pysnmp.hlapi import CommunityData, ContextData, ObjectIdentity, ObjectType, SnmpEngine, UdpTransportTarget, getCmd
        error_indication, error_status, error_index, var_binds = next(
            getCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((host, port), timeout=timeout),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
        )
        if error_indication:
            log.debug("SNMP error for %s/%s: %s", host, oid, error_indication)
            return None
        if error_status:
            log.debug("SNMP error status for %s/%s: %s", host, oid, error_status)
            return None
        if var_binds:
            return str(var_binds[0][1])
    except ImportError:
        log.warning("pysnmp nao instalado — instale com: pip install pysnmp")
        return None
    except Exception as e:
        log.debug("SNMP exception for %s/%s: %s", host, oid, e)
    return None


def snmp_walk(host: str, oid_prefix: str, community: str = "public", port: int = 161, timeout: int = 3) -> list[dict[str, str]]:
    try:
        from pysnmp.hlapi import CommunityData, ContextData, ObjectIdentity, ObjectType, SnmpEngine, UdpTransportTarget, nextCmd
        results = []
        for error_indication, error_status, error_index, var_binds in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((host, port), timeout=timeout),
            ContextData(),
            ObjectType(ObjectIdentity(oid_prefix)),
            lexicographicMode=False,
        ):
            if error_indication:
                break
            if error_status:
                break
            for name, val in var_binds:
                results.append({"oid": str(name), "value": str(val)})
        return results
    except ImportError:
        log.warning("pysnmp nao instalado")
        return []
    except Exception as e:
        log.debug("SNMP walk exception for %s/%s: %s", host, oid_prefix, e)
    return []


def snmp_get_printer_info(host: str, community: str = "public") -> dict:
    OIDS = {
        "toner_level": ".1.3.6.1.2.1.43.11.1.1.9.1.1",
        "toner_max": ".1.3.6.1.2.1.43.11.1.1.8.1.1",
        "page_count": ".1.3.6.1.2.1.43.10.2.1.4.1.1",
        "drum_life": ".1.3.6.1.2.1.43.12.1.1.4.1.1",
        "drum_max": ".1.3.6.1.2.1.43.12.1.1.5.1.1",
        "error_code": ".1.3.6.1.2.1.25.3.5.1.2.1",
        "error_message": ".1.3.6.1.2.1.43.18.1.1.8.1.1",
        "device_status": ".1.3.6.1.2.1.25.3.5.1.1.1",
    }
    result = {}
    for key, oid in OIDS.items():
        val = snmp_get(host, oid, community=community)
        if val is not None:
            result[key] = val
    return result
