#!/usr/bin/env python3
"""Verify real Nmap XML and reveal practice flags (maintainer spoilers)."""
import argparse
import ipaddress
import re
import shlex
import sys
from xml.etree import ElementTree as ET

NETWORK = ipaddress.ip_network("172.30.77.0/28")
PORTAL = "172.30.77.10"
ARCHIVE = "172.30.77.11"
MAX_XML_BYTES = 2 * 1024 * 1024
FLAGS = {
    "NM-01": "MFANO{h0sts_b3f0r3_p0rts}",
    "NM-02": "MFANO{c0nn3ct_sh0ws_0p3n_4nd_cl0s3d}",
    "NM-03": "MFANO{h1gh_p0rts_c0unt_t00}",
    "NM-04": "MFANO{pr0b3s_b34t_p0rt_gu3ss3s}",
    "NM-05": "MFANO{udp_n33ds_4_r34l_r3ply}",
    "NM-06": "MFANO{t1tl3s_4nd_h34d3rs_t3ll_4_st0ry}",
    "NM-07": "MFANO{r34d_0nly_scr1pts_f1nd_clu3s}",
    "NM-08": "MFANO{c3rt1f1c4t3_n4m3s_4r3_3v1d3nc3}",
    "NM-09": "MFANO{ssh_k3ys_1d3nt1fy_4_s3rv1c3}",
    "NM-10": "MFANO{4n0nym0us_l1sts_4r3_3num3r4t10n}",
    "NM-11": "MFANO{th3_s3c0nd_h0st_h4s_4_st0ry}",
    "NM-12": "MFANO{sc4n_r3c0rd_r3v13w_r3p34t}",
}


class EvidenceError(ValueError):
    """A scan has not demonstrated the exercise's finding yet."""


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def port_numbers(specification):
    numbers = set()
    for item in specification.split(","):
        if not item:
            continue
        pieces = item.split("-")
        require(len(pieces) in (1, 2) and all(part.isdecimal() for part in pieces),
                "The XML contains an invalid port range.")
        low, high = int(pieces[0]), int(pieces[-1])
        require(0 <= low <= high <= 65535, "The XML contains an invalid port range.")
        numbers.update(range(low, high + 1))
    return numbers


class Evidence:
    def __init__(self, data):
        require(0 < len(data) <= MAX_XML_BYTES, "Use one complete XML report smaller than 2 MiB.")
        # Nmap emits this simple DOCTYPE. External DTDs and entity declarations
        # are unnecessary for scan reports and must not be expanded by a checker.
        remaining = re.sub(br"<!DOCTYPE\s+nmaprun\s*>", b"", data)
        require(b"<!DOCTYPE" not in remaining and b"<!ENTITY" not in remaining,
                "External DTDs and entities are not accepted.")
        try:
            self.root = ET.fromstring(data)
        except ET.ParseError as exc:
            raise EvidenceError("The report is not complete, valid Nmap XML.") from exc
        require(self.root.tag == "nmaprun" and self.root.get("scanner") == "nmap",
                "Save Nmap XML with -oX or -oA; terminal text is not an XML report.")
        finished = self.root.find("runstats/finished")
        require(finished is not None and finished.get("exit") == "success",
                "Wait for the scan to finish successfully before checking its report.")
        try:
            self.arguments = shlex.split(self.root.get("args", ""))
        except ValueError as exc:
            raise EvidenceError("The report contains invalid scan arguments.") from exc
        self.hosts = {}
        for host in self.root.findall("host"):
            addresses = [item.get("addr", "") for item in host.findall("address")
                         if item.get("addrtype") in ("ipv4", "ipv6")]
            for address in addresses:
                try:
                    in_scope = ipaddress.ip_address(address) in NETWORK
                except ValueError as exc:
                    raise EvidenceError("The report contains an invalid host address.") from exc
                require(in_scope, "Use reports from the internal 172.30.77.0/28 practice network.")
                require(address not in self.hosts, "Use one scan report, without duplicated hosts.")
                self.hosts[address] = host
        self.scanned = {protocol: set() for protocol in ("tcp", "udp")}
        for info in self.root.findall("scaninfo"):
            if info.get("protocol") in self.scanned:
                self.scanned[info.get("protocol")].update(port_numbers(info.get("services", "")))

    def host(self, address=PORTAL):
        host = self.hosts.get(address)
        status = None if host is None else host.find("status")
        require(status is not None and status.get("state") == "up",
                f"The report must show the practice target {address} up.")
        return host

    def scan_type(self, kind, protocol):
        require(any(info.get("type") == kind and info.get("protocol") == protocol
                    for info in self.root.findall("scaninfo")),
                f"This exercise needs a {kind} {protocol.upper()} scan.")

    def port(self, number, protocol="tcp", address=PORTAL):
        host = self.host(address)
        matches = [port for port in host.findall("ports/port")
                   if port.get("protocol") == protocol and port.get("portid") == str(number)]
        require(len(matches) == 1, f"Missing {protocol.upper()} port {number} on {address}.")
        state = matches[0].find("state")
        require(state is not None and state.get("state") == "open",
                f"Port {number}/{protocol} must have a confirmed open state.")
        return matches[0]

    def closed_port(self, number, protocol="tcp"):
        host = self.host()
        for port in host.findall("ports/port"):
            if port.get("protocol") == protocol and port.get("portid") == str(number):
                state = port.find("state")
                return state is not None and state.get("state") == "closed"
        # Nmap normally compresses closed ports into extraports. Newer releases
        # list their ranges; older releases can be inferred when one aggregate
        # accounts for every scanned port absent from the explicit port list.
        aggregates = host.findall("ports/extraports")
        for aggregate in aggregates:
            for reason in aggregate.findall("extrareasons"):
                if reason.get("proto", protocol) == protocol and reason.get("ports"):
                    if number in port_numbers(reason.get("ports")):
                        return aggregate.get("state") == "closed"
        if len(aggregates) == 1 and number in self.scanned[protocol]:
            explicit = {int(port.get("portid")) for port in host.findall("ports/port")
                        if port.get("protocol") == protocol}
            missing = self.scanned[protocol] - explicit
            only_protocol = sum(bool(ports) for ports in self.scanned.values()) == 1
            return (only_protocol and number in missing and aggregates[0].get("state") == "closed"
                    and aggregates[0].get("count") == str(len(missing)))
        return False

    def service(self, number, name, protocol="tcp", address=PORTAL, *, product=None, tunnel=None):
        service = self.port(number, protocol, address).find("service")
        require(service is not None and service.get("method") == "probed" and service.get("name") == name,
                f"Use version detection to confirm the service on {number}/{protocol}.")
        if product:
            require(product.lower() in service.get("product", "").lower() and service.get("version"),
                    f"The report needs a detected product and version on {number}/{protocol}.")
        if tunnel:
            require(service.get("tunnel") == tunnel, "Confirm the TLS-wrapped service with version detection.")

    def script(self, number, name, protocol="tcp", address=PORTAL):
        script = self.port(number, protocol, address).find(f"script[@id='{name}']")
        require(script is not None, f"Include the named NSE script {name} in this report.")
        text = script.get("output", "") + " " + " ".join(script.itertext())
        require(text.strip() and "ERROR:" not in text, f"The {name} script must return a successful finding.")
        return text

    def web(self, number=80, address=PORTAL, *, archive=False):
        title = "Mfano Archive Inventory" if archive else "Mfano Network Practice"
        role = "archive" if archive else "portal"
        require(title in self.script(number, "http-title", address=address), "Record the practice site's title.")
        headers = self.script(number, "http-headers", address=address).lower()
        require(f"x-lab-role: {role}" in headers, "Record the site's role response header.")

    def certificate(self):
        text = self.script(443, "ssl-cert")
        require("portal.mfano.test" in text and "archive.mfano.test" in text,
                "Record both practice names from the TLS certificate.")

    def ssh_key(self):
        text = self.script(22, "ssh-hostkey")
        require("rsa" in text.lower() and re.search(r"[0-9a-f]{2}(?::[0-9a-f]{2}){15}|[0-9a-f]{32}|SHA256:", text),
                "Record an RSA host-key fingerprint without signing in.")

    def dns(self):
        self.scan_type("udp", "udp")
        self.service(53, "domain", "udp")
        require("dnsmasq" in self.script(53, "dns-nsid", "udp").lower(),
                "Record the training DNS server's version reply with dns-nsid.")


def check(stage, data):
    require(stage in FLAGS, "Choose an exercise from NM-01 through NM-12.")
    evidence = Evidence(data)
    if stage == "NM-01":
        evidence.host(PORTAL)
        evidence.host(ARCHIVE)
        require(not any(evidence.scanned.values()), "Use host discovery without a port scan for NM-01.")
    elif stage == "NM-02":
        evidence.scan_type("connect", "tcp")
        for number in (21, 22, 80, 443):
            evidence.port(number)
        require(evidence.closed_port(9999), "Include the closed control port in your TCP connect scan.")
    elif stage == "NM-03":
        evidence.scan_type("syn", "tcp")
        require(evidence.scanned["tcp"] == set(range(1, 65536)), "Scan the full TCP port range for NM-03.")
        evidence.port(31337)
    elif stage == "NM-04":
        evidence.service(21, "ftp", product="vsftpd")
        evidence.service(22, "ssh", product="OpenSSH")
        evidence.service(80, "http")
        evidence.service(443, "http", tunnel="ssl")
    elif stage == "NM-05":
        evidence.dns()
    elif stage == "NM-06":
        evidence.web()
    elif stage == "NM-07":
        robots = evidence.script(80, "http-robots.txt")
        require("/staff-notices/" in robots and "/archive-transfer/" in robots,
                "Record both crawler exclusions with http-robots.txt.")
        methods = set(re.findall(r"\b[A-Z]+\b", evidence.script(80, "http-methods")))
        require({"GET", "HEAD", "OPTIONS"} <= methods, "Record the advertised read-only HTTP methods.")
    elif stage == "NM-08":
        evidence.certificate()
    elif stage == "NM-09":
        evidence.ssh_key()
    elif stage == "NM-10":
        text = evidence.script(21, "ftp-anon")
        require("Anonymous FTP login allowed" in text and "handover.txt" in text,
                "Record anonymous read-only access and its directory listing.")
    elif stage == "NM-11":
        evidence.service(18080, "http", address=ARCHIVE)
        evidence.web(18080, ARCHIVE, archive=True)
    elif stage == "NM-12":
        evidence.scan_type("syn", "tcp")
        evidence.dns()
        evidence.service(53, "domain")
        evidence.service(21, "ftp", product="vsftpd")
        evidence.service(22, "ssh", product="OpenSSH")
        evidence.service(80, "http")
        evidence.service(443, "http", tunnel="ssl")
        evidence.service(31337, "http")
        evidence.web()
        evidence.certificate()
        evidence.ssh_key()
        require(any(argument == "-oA" or argument.startswith("-oA") for argument in evidence.arguments),
                "Save the final inventory with -oA, then check its .xml report.")
    return FLAGS[stage]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check",))
    parser.add_argument("stage", choices=tuple(FLAGS))
    args = parser.parse_args()
    try:
        print(check(args.stage, sys.stdin.buffer.read(MAX_XML_BYTES + 1)))
    except EvidenceError as exc:
        print(f"Not yet: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
