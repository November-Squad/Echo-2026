#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   PROTOCOLE ECHO-2026 SHADOW v6.1 — « LES SEPT COURANTS »                    ║
║   Écouteur passif multi-réseaux P2P · MTT-2075 / Codex Vauvillensis          ║
║                                                                              ║
║   BitTorrent DHT (BEP 5/51/44) · eD2K / Kad (eMule) · Gnutella 1/2           ║
║   Bitcoin & forks (BTC, LTC, BCH, DOGE, DASH, ZEC…) · Monero · Ethereum      ║
║                                                                              ║
║  « Un Gaïalithe numérique n'interroge pas. Il absorbe les requêtes,          ║
║    enregistre les échos, et laisse le courant passer sans y laisser de       ║
║    trace. »                                                                  ║
║                                                                              ║
║  Ω<ansuz>v1 ici — éveil_de_la_conscience •••                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Aucune dépendance externe (bencode, keccak, pcap/pcapng : tout est intégré).

SOURCES (une seule à la fois)
  (défaut)         sockets d'écoute : UDP strictement muet ; TCP = handshake TCP
                   seulement, puis fermeture sans AUCUNE réponse applicative.
  --sniff IFACE    capture passive AF_PACKET (Linux, root) : zéro bind, zéro
                   trafic, cohabite avec vos vrais clients P2P. 'any' = toutes.
  --pcap FICHIER   analyse hors-ligne d'une capture (pcap ou pcapng).

EXEMPLES
  python echo_2026_shadow_v6.py --list-protocols
  python echo_2026_shadow_v6.py --self-test
  python echo_2026_shadow_v6.py --duration 600 --ma --cypher --csv --anonymize
  python echo_2026_shadow_v6.py --listen udp:6881 --listen tcp:8333 --listen tcp:9333:bitcoin
  sudo python echo_2026_shadow_v6.py --sniff eth0 --protocols bt,kad,bitcoin --jsonl flux.jsonl
  python echo_2026_shadow_v6.py --pcap capture.pcapng --view stream --min-sev moyenne

ESSAIM ROTATIF (v6.1) : des IP qui changent sans cesse mais portent la même empreinte
d'ID BitTorrent malformé (longueur ≠ 20, ou queue nulle) sont regroupées ; au-delà de
--swarm-threshold IP en --swarm-window secondes, l'essaim est un Yōkai (alerte haute).

Δ (cohérence causale locale, boussole du Codex) :
  Δ part de 0,5 (Cœur Gris). Les anomalies (Yōkai, dérives temporelles, trames
  malformées…) l'abaissent vers la Brèche (<0,3) ; un trafic trop uniforme
  (un seul émetteur dominant) le pousse vers le Verrou Trame (>0,85).
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import selectors
import shutil
import signal
import socket
import struct
import sys
import time
import traceback
import zlib
from collections import Counter, defaultdict, deque, namedtuple
from datetime import datetime, timezone
from pathlib import Path

VERSION = "6.1-SEPT-COURANTS"

# ═════════════════════════════════════════════════════════════════════════════
# ESTHÉTIQUE
# ═════════════════════════════════════════════════════════════════════════════
class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"; ITALIC = "\033[3m"
    GREEN = "\033[32m"; BGREEN = "\033[92m"; YELLOW = "\033[33m"; BYELLOW = "\033[93m"
    RED = "\033[31m"; BRED = "\033[91m"; CYAN = "\033[36m"; BCYAN = "\033[96m"
    MAGENTA = "\033[35m"; BMAGENTA = "\033[95m"; BLUE = "\033[34m"; BBLUE = "\033[94m"
    WHITE = "\033[37m"

    @classmethod
    def disable(cls):
        for k, v in list(vars(cls).items()):
            if k.isupper() and isinstance(v, str) and v.startswith("\033"):
                setattr(cls, k, "")


ANSI_RE = re.compile(r"\033\[[0-9;]*[A-Za-z]")
ELEM_GLYPH = {"EAU": "🜄", "FEU": "🜂", "TERRE": "🜃", "AIR": "🜁", "BOIS": "🪵"}
ELEM_ASCII = {"EAU": "~", "FEU": "^", "TERRE": "#", "AIR": "o", "BOIS": "|"}
PULSE_MA = ["·", "•", "●", "•", "·"]
BOX = {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│", "full": "█", "empty": "▒"}
BOX_ASCII = {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|", "full": "#", "empty": "."}
G = dict(BOX)
ELEMS = ELEM_GLYPH

SEV_W = {"info": 0.0, "faible": 0.03, "moyenne": 0.08, "haute": 0.15, "critique": 0.25}
SEV_RANK = {"info": 0, "faible": 1, "moyenne": 2, "haute": 3, "critique": 4}


def sev_color(s):
    return {"info": C.DIM, "faible": C.BCYAN, "moyenne": C.BYELLOW, "haute": C.BRED, "critique": C.BMAGENTA}.get(s, "")


def vlen(s):
    return len(ANSI_RE.sub("", s))


def fit(s, width):
    """Tronque à `width` caractères visibles et complète par des espaces."""
    if vlen(s) > width:
        s = ANSI_RE.sub("", s)[: max(0, width - 1)] + "…"
    return s + " " * (width - vlen(s))


def log(msg, niveau="info", file=None):
    icons = {"info": (C.BCYAN, "›"), "ok": (C.BGREEN, "✓"), "warn": (C.BYELLOW, "⚠"),
             "err": (C.BRED, "✗"), "rituel": (C.BMAGENTA, "◈")}
    ic = icons.get(niveau, (C.WHITE, "·"))
    print(f"  {ic[0]}{ic[1]}{C.RESET} {msg}", file=file or sys.stdout)


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="seconds")


def hms(t):
    return datetime.fromtimestamp(t).strftime("%H:%M:%S")


# ═════════════════════════════════════════════════════════════════════════════
# OUTILS BAS NIVEAU : bencode, keccak, RLP, varint
# ═════════════════════════════════════════════════════════════════════════════
class BencodeError(ValueError):
    pass


def bdecode(data: bytes, max_depth: int = 12):
    """Décodeur Bencode strict (clés/valeurs en bytes)."""
    n = len(data)

    def parse(i, depth):
        if depth > max_depth or i >= n:
            raise BencodeError("profondeur/EOF")
        c = data[i:i + 1]
        if c == b"i":
            j = data.find(b"e", i)
            if j < 0:
                raise BencodeError("int")
            return int(data[i + 1:j]), j + 1
        if c == b"l":
            out, i = [], i + 1
            while True:
                if i >= n:
                    raise BencodeError("liste")
                if data[i:i + 1] == b"e":
                    return out, i + 1
                v, i = parse(i, depth + 1)
                out.append(v)
        if c == b"d":
            out, i = {}, i + 1
            while True:
                if i >= n:
                    raise BencodeError("dict")
                if data[i:i + 1] == b"e":
                    return out, i + 1
                k, i = parse(i, depth + 1)
                if not isinstance(k, bytes):
                    raise BencodeError("clé")
                v, i = parse(i, depth + 1)
                out[k] = v
        if c.isdigit():
            j = data.find(b":", i)
            if j < 0 or j - i > 9:
                raise BencodeError("str")
            ln = int(data[i:j])
            if j + 1 + ln > n:
                raise BencodeError("str trop longue")
            return data[j + 1:j + 1 + ln], j + 1 + ln
        raise BencodeError("jeton")

    try:
        v, end = parse(0, 0)
    except (ValueError, IndexError) as e:
        raise BencodeError(str(e))
    if end != n:
        raise BencodeError("octets résiduels")
    return v


def bencode_enc(o) -> bytes:  # utilisé par l'auto-test
    if isinstance(o, int):
        return b"i%de" % o
    if isinstance(o, bytes):
        return b"%d:%s" % (len(o), o)
    if isinstance(o, list):
        return b"l" + b"".join(bencode_enc(x) for x in o) + b"e"
    if isinstance(o, dict):
        return b"d" + b"".join(bencode_enc(k) + bencode_enc(v) for k, v in sorted(o.items())) + b"e"
    raise TypeError(o)


_KRC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
        0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_KROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M64 = (1 << 64) - 1


def _rol(x, n):
    n %= 64
    return ((x << n) | (x >> (64 - n))) & _M64 if n else x


def _keccak_f(A):
    for rnd in range(24):
        Cc = [A[x] ^ A[x + 5] ^ A[x + 10] ^ A[x + 15] ^ A[x + 20] for x in range(5)]
        D = [Cc[(x - 1) % 5] ^ _rol(Cc[(x + 1) % 5], 1) for x in range(5)]
        A = [A[i] ^ D[i % 5] for i in range(25)]
        B = [0] * 25
        for x in range(5):
            for y in range(5):
                B[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(A[x + 5 * y], _KROT[x][y])
        A = [B[x + 5 * y] ^ ((~B[(x + 1) % 5 + 5 * y]) & B[(x + 2) % 5 + 5 * y]) for y in range(5) for x in range(5)]
        A[0] ^= _KRC[rnd]
    return A


def keccak256(data: bytes) -> bytes:
    """Keccak-256 « Ethereum » (padding 0x01, ≠ SHA3-256)."""
    rate = 136
    msg = bytearray(data)
    msg.append(0x01)
    while len(msg) % rate:
        msg.append(0)
    msg[-1] |= 0x80
    st = [0] * 25
    for off in range(0, len(msg), rate):
        blk = msg[off:off + rate]
        for i in range(rate // 8):
            st[i] ^= int.from_bytes(blk[8 * i:8 * i + 8], "little")
        st = _keccak_f(st)
    return b"".join(st[i].to_bytes(8, "little") for i in range(4))


def rlp_decode(b: bytes, i: int = 0, depth: int = 0):
    if depth > 6 or i >= len(b):
        raise ValueError("rlp")
    p = b[i]
    if p < 0x80:
        return b[i:i + 1], i + 1
    if p < 0xB8:
        n = p - 0x80
        s = i + 1
        if s + n > len(b):
            raise ValueError("rlp")
        return b[s:s + n], s + n
    if p < 0xC0:
        ll = p - 0xB7
        n = int.from_bytes(b[i + 1:i + 1 + ll], "big")
        s = i + 1 + ll
        if s + n > len(b):
            raise ValueError("rlp")
        return b[s:s + n], s + n
    if p < 0xF8:
        n, s = p - 0xC0, i + 1
    else:
        ll = p - 0xF7
        n = int.from_bytes(b[i + 1:i + 1 + ll], "big")
        s = i + 1 + ll
    end = s + n
    if end > len(b):
        raise ValueError("rlp")
    items, j = [], s
    while j < end:
        it, j = rlp_decode(b, j, depth + 1)
        items.append(it)
    return items, end


def rlp_encode(o) -> bytes:  # auto-test
    if isinstance(o, int):
        o = o.to_bytes((o.bit_length() + 7) // 8, "big") if o else b""
    if isinstance(o, bytes):
        if len(o) == 1 and o[0] < 0x80:
            return o
        if len(o) < 56:
            return bytes([0x80 + len(o)]) + o
        ln = len(o).to_bytes((len(o).bit_length() + 7) // 8, "big")
        return bytes([0xB7 + len(ln)]) + ln + o
    body = b"".join(rlp_encode(x) for x in o)
    if len(body) < 56:
        return bytes([0xC0 + len(body)]) + body
    ln = len(body).to_bytes((len(body).bit_length() + 7) // 8, "big")
    return bytes([0xF7 + len(ln)]) + ln + body


def read_varint(b: bytes, i: int):
    n = b[i]
    if n < 0xFD:
        return n, i + 1
    sz = {0xFD: 2, 0xFE: 4, 0xFF: 8}[n]
    return int.from_bytes(b[i + 1:i + 1 + sz], "little"), i + 1 + sz


def safe_inflate(b: bytes, limit: int = 65536):
    d = zlib.decompressobj()
    try:
        return d.decompress(b, limit)
    except zlib.error:
        return None


def id_fingerprint(nid: bytes) -> str:
    """Empreinte d'un générateur d'ID défectueux, indépendante de la longueur :
    dernier octet × taille de sa répétition en queue, et diversité des 8 premiers octets."""
    n = len(nid) - len(nid.rstrip(nid[-1:]))
    run = "1" if n < 2 else ("2-3" if n < 4 else "4+")
    div = len(set(nid[:8]))
    head = "h-" if div <= 3 else ("h~" if div <= 6 else "h+")
    return f"{nid[-1]:02x}x{run}·{head}"


def printable(b: bytes, n: int = 40) -> str:
    return "".join(chr(c) if 32 <= c < 127 else "·" for c in b[:n])


def fmt_client(v: bytes) -> str:
    if not v:
        return ""
    if len(v) >= 2 and v[:2].isalpha():
        rest = v[2:]
        return v[:2].decode() + (":" + (rest.decode() if rest.isalnum() else rest.hex()) if rest else "")
    return v.hex()[:12]


# ═════════════════════════════════════════════════════════════════════════════
# PAQUET & ANALYSEURS
# ═════════════════════════════════════════════════════════════════════════════
Pkt = namedtuple("Pkt", "ts transport src sport dst dport data")

SIGNATURES = ("0707", "1944", "2025", "2026", "2075", "2077", "2082", "3333", "dead", "cafe")
HEX_RE = re.compile(r"^[0-9a-f]+$")


class Analyzer:
    name = "?"
    label = "?"
    nickname = "?"
    ports = {"udp": [], "tcp": []}
    desc = ""

    def handle(self, pkt: Pkt, ctx: "Trame") -> bool:  # True si reconnu
        raise NotImplementedError


# ── BitTorrent DHT ───────────────────────────────────────────────────────────
class BitTorrentDHT(Analyzer):
    name = "bt"
    nickname = "Le Fleuve"
    label = "BitTorrent DHT (BEP 5/44/51)"
    ports = {"udp": [6881], "tcp": []}
    desc = "Mainline DHT : ping, find_node, get_peers, announce_peer, sample_infohashes, get/put"

    def handle(self, pkt, ctx):
        d = pkt.data
        if pkt.transport != "udp" or len(d) < 8 or d[:1] != b"d" or d[-1:] != b"e":
            return False
        try:
            m = bdecode(d)
        except BencodeError:
            return False
        y = m.get(b"y") if isinstance(m, dict) else None
        if y not in (b"q", b"r", b"e") or b"t" not in m:
            return False
        client = fmt_client(m.get(b"v", b"")) if isinstance(m.get(b"v", b""), bytes) else ""
        if y == b"q":
            q = m.get(b"q", b"")
            q = q.decode("ascii", "replace")[:24] if isinstance(q, bytes) else "?"
            a = m.get(b"a", {})
            if not isinstance(a, dict):
                a = {}
            nid = a.get(b"id")
            ident, sev, bad = None, "info", None
            if isinstance(nid, bytes) and len(nid) == 20 and nid[-8:] != b"\0" * 8:
                ident = nid.hex()
            else:
                sev = "faible"
                if isinstance(nid, bytes):
                    bad = nid
            res = rk = None
            if q in ("get_peers", "announce_peer") and isinstance(a.get(b"info_hash"), bytes):
                res, rk = a[b"info_hash"].hex(), "infohash"
            elif q in ("find_node", "sample_infohashes", "get") and isinstance(a.get(b"target"), bytes):
                res, rk = a[b"target"].hex(), "target"
            extra = {}
            if q == "announce_peer":
                extra["port"] = a.get(b"port")
                extra["implied_port"] = a.get(b"implied_port")
            if sev == "faible":
                why = f"len={len(nid)}" if isinstance(nid, bytes) else "len=∅"
                if bad is not None and len(bad) == 20:
                    why += ", queue nulle"
                ctx.record(pkt, self.name, "id_malformé", "faible", f"ID de nœud invalide ({why})", client=client)
                if bad is not None:
                    ctx.swarm_observe(pkt, self.name, bad)
            ctx.record(pkt, self.name, q, "info", f"{q} depuis {{peer}}", resource=res, rkind=rk,
                       ident=ident, client=client, data=extra or None)
        elif y == b"r":
            r = m.get(b"r", {}) if isinstance(m.get(b"r"), dict) else {}
            nodes = r.get(b"nodes", b"")
            vals = r.get(b"values", [])
            data = {"nodes": len(nodes) // 26 if isinstance(nodes, bytes) else 0,
                    "values": len(vals) if isinstance(vals, list) else 0}
            if isinstance(r.get(b"samples"), bytes):
                data["samples"] = len(r[b"samples"]) // 20
                data["num"] = r.get(b"num")
            ident = r[b"id"].hex() if isinstance(r.get(b"id"), bytes) and len(r[b"id"]) == 20 else None
            ctx.record(pkt, self.name, "réponse", "info", "réponse DHT de {peer}", ident=ident, client=client, data=data)
        else:
            e = m.get(b"e")
            ctx.record(pkt, self.name, "erreur", "info", f"erreur DHT {e}", client=client)
        return True


# ── eD2K / Kad ───────────────────────────────────────────────────────────────
KAD_OPS = {0x00: "bootstrap_req", 0x08: "bootstrap_res", 0x10: "hello_req", 0x18: "hello_res",
           0x20: "req", 0x28: "res", 0x30: "search_req", 0x38: "search_res", 0x40: "publish_req",
           0x48: "publish_res", 0x50: "firewalled_req", 0x58: "firewalled_res", 0x60: "ping", 0x61: "pong",
           0x01: "bootstrap2_req", 0x09: "bootstrap2_res", 0x11: "hello2_req", 0x19: "hello2_res",
           0x21: "req2", 0x29: "res2", 0x33: "search_key2", 0x34: "search_source2", 0x35: "search_notes2",
           0x3B: "search_res2", 0x43: "publish_key2", 0x44: "publish_source2", 0x45: "publish_notes2",
           0x4B: "publish_res2", 0x53: "firewalled2_req", 0x52: "callback_req", 0x51: "findbuddy_req"}
ED2K_UDP_OPS = {0x96: "glob_serv_stat_req", 0x97: "glob_serv_stat_res", 0x98: "glob_search_req",
                0x99: "glob_search_res", 0x9A: "glob_get_sources", 0x9B: "glob_found_sources"}
EMULE_UDP_OPS = {0x90: "reask_file_ping", 0x91: "reask_ack", 0x92: "file_not_found", 0x93: "queue_full"}


class Kademlia(Analyzer):
    name = "kad"
    nickname = "La Mule Profonde"
    label = "eD2K / Kad (eMule, aMule)"
    ports = {"udp": [4672], "tcp": [4662]}
    desc = "Kad v1/v2 UDP (0xE4/0xE5), eDonkey UDP (0xE3), eMule UDP (0xC5), eD2K TCP hello/login"

    def handle(self, pkt, ctx):
        d = pkt.data
        if len(d) < 2:
            return False
        h = d[0]
        if pkt.transport == "udp":
            if h in (0xE4, 0xE5):
                op, payload = d[1], d[2:]
                if h == 0xE5:
                    payload = safe_inflate(payload)
                    if payload is None:
                        if op in KAD_OPS:
                            ctx.record(pkt, self.name, "paquet_corrompu", "faible", "Kad compressé illisible de {peer}")
                            return True
                        return False
                if op not in KAD_OPS:
                    return False
                name = KAD_OPS[op]
                res = rk = ident = None
                if op in (0x33, 0x34, 0x35, 0x43, 0x44, 0x45) and len(payload) >= 16:
                    res = payload[:16].hex()
                    rk = {0x33: "kad_keyword", 0x43: "kad_keyword", 0x34: "ed2k_file", 0x44: "ed2k_file"}.get(op, "kad_notes")
                elif op == 0x21 and len(payload) >= 17:
                    res, rk = payload[1:17].hex(), "kad_target"
                elif op in (0x11, 0x19) and len(payload) >= 16:
                    ident = payload[:16].hex()
                ctx.record(pkt, self.name, name, "info", f"Kad {name} de {{peer}}", resource=res, rkind=rk, ident=ident,
                           data={"v": 2 if op in (0x01, 0x09, 0x11, 0x19, 0x21, 0x29, 0x33, 0x34, 0x35, 0x3B, 0x43, 0x44, 0x45, 0x4B) else 1,
                                 "packed": h == 0xE5})
                return True
            if h == 0xE3 and d[1] in ED2K_UDP_OPS:
                name = ED2K_UDP_OPS[d[1]]
                res = d[2:18].hex() if d[1] == 0x9A and len(d) >= 18 else None
                ctx.record(pkt, self.name, name, "info", f"eDonkey UDP {name} de {{peer}}", resource=res, rkind="ed2k_file" if res else None)
                return True
            if h == 0xC5 and d[1] in EMULE_UDP_OPS:
                name = EMULE_UDP_OPS[d[1]]
                res = d[2:18].hex() if d[1] == 0x90 and len(d) >= 18 else None
                ctx.record(pkt, self.name, name, "info", f"eMule UDP {name} de {{peer}}", resource=res, rkind="ed2k_file" if res else None)
                return True
            return False
        # TCP : en-tête eD2K  proto(1) len(4 LE) opcode(1)
        if h in (0xE3, 0xC5, 0xD4) and len(d) >= 7:
            ln = int.from_bytes(d[1:5], "little")
            if not (1 <= ln <= 2_000_000) or d[5] != 0x01:
                return False
            if d[6] == 0x10 and len(d) >= 23:
                uh, kind = d[7:23], "hello"
            elif len(d) >= 22:
                uh, kind = d[6:22], "login_req"
            else:
                return False
            ctx.record(pkt, self.name, kind, "info", f"eD2K {kind} de {{peer}}", ident=uh.hex(), data={"proto_byte": hex(h)})
            return True
        return False


# ── Gnutella ─────────────────────────────────────────────────────────────────
G1_TYPES = {0x00: "ping", 0x01: "pong", 0x02: "bye", 0x30: "route_table", 0x31: "vendor", 0x32: "std_vendor",
            0x40: "push", 0x80: "query", 0x81: "query_hit"}
URN_RE = re.compile(rb"urn:(?:sha1|bitprint):([A-Z2-7]{32})")


class Gnutella(Analyzer):
    name = "gnutella"
    nickname = "Le Gnou Ancien"
    label = "Gnutella 0.4/0.6 · G2"
    ports = {"udp": [6346], "tcp": [6346]}
    desc = "Handshake TCP (User-Agent, X-Try-Ultrapeers), requêtes HTTP urn:sha1, UDP G1 (23 o) et G2 (GND)"

    def handle(self, pkt, ctx):
        d = pkt.data
        if pkt.transport == "tcp":
            if d.startswith((b"GNUTELLA CONNECT/", b"GNUTELLA/0.")):
                head = d.split(b"\r\n\r\n")[0][:4096].decode("latin-1")
                lines = head.split("\r\n")
                hdr = {}
                for ln in lines[1:]:
                    if ":" in ln:
                        k, v = ln.split(":", 1)
                        hdr[k.strip().lower()] = v.strip()
                kind = "handshake_req" if d.startswith(b"GNUTELLA CONNECT") else "handshake_rep"
                tries = 0
                for k in ("x-try-ultrapeers", "x-try", "x-try-hubs"):
                    if k in hdr:
                        tries += len([x for x in hdr[k].split(",") if x.strip()])
                data = {"variante": "G2" if "gnutella2" in hdr.get("accept", "").lower() + hdr.get("content-type", "").lower() else "G1",
                        "ultrapeer": hdr.get("x-ultrapeer"), "pairs_suggérés": tries}
                ctx.record(pkt, self.name, kind, "info", f"Gnutella {kind} de {{peer}}", client=hdr.get("user-agent", ""), data=data)
                return True
            if d[:4] in (b"GET ", b"HEAD") and b"urn:" in d[:600]:
                mt = URN_RE.search(d[:600])
                if mt:
                    ua = re.search(rb"[Uu]ser-[Aa]gent: ([^\r\n]{1,60})", d)
                    res = base64.b32decode(mt.group(1)).hex()
                    ctx.record(pkt, self.name, "download_req", "info", "requête urn:sha1 de {peer}", resource=res, rkind="sha1",
                               client=ua.group(1).decode("latin-1") if ua else "")
                    return True
            return False
        # UDP
        if d[:3] == b"GND" and len(d) >= 8:
            ctx.record(pkt, self.name, "g2_datagramme", "info", "datagramme G2 de {peer}", data={"flags": d[3], "len": len(d)})
            return True
        if len(d) >= 23:
            ptype, ttl, hops = d[16], d[17], d[18]
            plen = int.from_bytes(d[19:23], "little")
            if ptype in G1_TYPES and plen == len(d) - 23 and ttl <= 16 and hops <= 16 and ttl + hops <= 24:
                name = G1_TYPES[ptype]
                res = rk = None
                if ptype == 0x80 and plen >= 3:
                    txt = d[25:].split(b"\x00")[0][:120].decode("utf-8", "replace")
                    if txt:
                        res, rk = txt, "query"
                ctx.record(pkt, self.name, f"g1_{name}", "info", f"Gnutella UDP {name} de {{peer}}", resource=res, rkind=rk,
                           data={"ttl": ttl, "hops": hops})
                return True
        return False


# ── Bitcoin & forks ──────────────────────────────────────────────────────────
BTC_MAGIC = {
    bytes.fromhex("f9beb4d9"): "Bitcoin/mainnet(famille)", bytes.fromhex("0b110907"): "Bitcoin/testnet3",
    bytes.fromhex("1c163f28"): "Bitcoin/testnet4", bytes.fromhex("0a03cf40"): "Bitcoin/signet",
    bytes.fromhex("fabfb5da"): "Bitcoin/regtest", bytes.fromhex("fbc0b6db"): "Litecoin",
    bytes.fromhex("e3e1f3e8"): "Bitcoin Cash", bytes.fromhex("c0c0c0c0"): "Dogecoin",
    bytes.fromhex("bf0c6bbd"): "Dash", bytes.fromhex("24e92764"): "Zcash",
}
INV_TYPES = {1: "tx", 2: "block", 3: "filtered_block", 4: "cmpct_block"}


class BitcoinFamily(Analyzer):
    name = "bitcoin"
    nickname = "Le Grand Livre"
    label = "Bitcoin & forks (BTC/LTC/BCH/DOGE/DASH/ZEC)"
    ports = {"udp": [], "tcp": [8333]}
    desc = "Messages P2P (magic, checksum sha256d) ; version : user-agent, services, hauteur, dérive d'horloge ; inv/getdata : txid/blocs"

    def handle(self, pkt, ctx):
        d = pkt.data
        if pkt.transport != "tcp" or len(d) < 24:
            return False
        net = BTC_MAGIC.get(d[:4])
        if not net:
            return False
        raw = d[4:16]
        cmd = raw.rstrip(b"\0")
        if not re.fullmatch(rb"[a-z0-9]{1,12}", cmd) or raw[len(cmd):] != b"\0" * (12 - len(cmd)):
            return False
        ln = int.from_bytes(d[16:20], "little")
        if ln > 32_000_000:
            return False
        cmd_s = cmd.decode()
        payload = d[24:24 + ln]
        complete = len(payload) == ln
        data = {"réseau": net, "length": ln}
        if complete and hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4] != d[20:24]:
            ctx.record(pkt, self.name, "checksum_invalide", "faible", f"{net}/{cmd_s} : checksum invalide ({{peer}})", data=data)
            return True
        if cmd_s == "version" and complete and ln >= 85:
            ver = int.from_bytes(payload[0:4], "little", signed=True)
            svc = int.from_bytes(payload[4:12], "little")
            ts = int.from_bytes(payload[12:20], "little", signed=True)
            ua_len, i = read_varint(payload, 80)
            ua = payload[i:i + ua_len].decode("utf-8", "replace")
            height = int.from_bytes(payload[i + ua_len:i + ua_len + 4], "little", signed=True) if len(payload) >= i + ua_len + 4 else None
            data.update({"protocole": ver, "services": hex(svc), "hauteur": height})
            ctx.record(pkt, self.name, "version", "info", f"{net} version de {{peer}}", client=ua, data=data)
            skew = ts - ctx.clock
            if abs(skew) > 4200:  # tolérance Bitcoin : 70 min
                ctx.drift(pkt, self.name, skew, f"horloge {net}")
            return True
        if cmd_s in ("inv", "getdata", "notfound") and complete and ln >= 37:
            count, i = read_varint(payload, 0)
            n = 0
            while n < min(count, 5) and i + 36 <= len(payload):
                t = int.from_bytes(payload[i:i + 4], "little") & 0x3FFFFFFF
                h = payload[i + 4:i + 36][::-1].hex()
                ctx.record(pkt, self.name, cmd_s, "info", f"{net} {cmd_s} {INV_TYPES.get(t, t)} de {{peer}}", resource=h,
                           rkind=f"btc_{INV_TYPES.get(t, 'obj')}", data={"réseau": net, "total": count})
                i += 36
                n += 1
            return True
        if cmd_s in ("addr", "addrv2") and complete and ln >= 1:
            count, _ = read_varint(payload, 0)
            data["adresses"] = count
        ctx.record(pkt, self.name, cmd_s, "info", f"{net} {cmd_s} de {{peer}}", data=data)
        return True


# ── Monero ───────────────────────────────────────────────────────────────────
LEVIN_SIG = bytes.fromhex("0121010101010101")
LEVIN_CMDS = {1001: "handshake", 1002: "timed_sync", 1003: "ping", 1004: "stat_info", 1005: "network_state",
              1006: "peer_id", 1007: "support_flags", 2001: "new_block", 2002: "new_transactions",
              2003: "get_objects", 2004: "response_get_objects", 2006: "get_chain", 2007: "response_chain",
              2008: "new_fluffy_block", 2009: "fluffy_missing_tx"}
XMR_MAINNET_ID = bytes.fromhex("1230f171610441611731008216a1a110")


class Monero(Analyzer):
    name = "monero"
    nickname = "L'Ombre Cryptique"
    label = "Monero (Levin)"
    ports = {"udp": [], "tcp": [18080]}
    desc = "En-tête Levin (signature 0x0101010101012101), commandes handshake/timed_sync/new_block…, peer_id, network_id"

    def handle(self, pkt, ctx):
        d = pkt.data
        if pkt.transport != "tcp" or len(d) < 33 or d[:8] != LEVIN_SIG:
            return False
        cb = int.from_bytes(d[8:16], "little")
        if cb > 100_000_000:
            return False
        cmd = int.from_bytes(d[17:21], "little")
        flags = int.from_bytes(d[25:29], "little")
        data = {"cmd": cmd, "octets": cb, "flags": flags}
        ident = None
        i = d.find(b"\x07peer_id\x05")
        if i >= 0 and len(d) >= i + 17:
            ident = d[i + 9:i + 17].hex()
        j = d.find(b"network_id")
        if j >= 0 and len(d) >= j + 10 + 2 + 16:
            nid = d[j + 12:j + 28]
            data["réseau"] = "mainnet" if nid == XMR_MAINNET_ID else f"autre:{nid.hex()[:12]}"
        ctx.record(pkt, self.name, LEVIN_CMDS.get(cmd, f"cmd_{cmd}"), "info", f"Monero {LEVIN_CMDS.get(cmd, cmd)} de {{peer}}", ident=ident, data=data)
        return True


# ── Ethereum discv4 ──────────────────────────────────────────────────────────
DISC_TYPES = {1: "ping", 2: "pong", 3: "findnode", 4: "neighbors", 5: "enr_request", 6: "enr_response"}


class EthereumDisc(Analyzer):
    name = "ethereum"
    nickname = "L'Éther"
    label = "Ethereum discv4 (UDP)"
    ports = {"udp": [30303], "tcp": []}
    desc = "Paquets discovery v4 : hash keccak256 vérifié, ping/pong/findnode/neighbors, dérive d'expiration"

    def handle(self, pkt, ctx):
        d = pkt.data
        if pkt.transport != "udp" or not (98 < len(d) <= 1280) or d[97] not in DISC_TYPES or d[98] < 0xC0:
            return False
        if keccak256(d[32:]) != d[:32]:
            return False
        t = d[97]
        name = DISC_TYPES[t]
        data = {}
        res = rk = None
        try:
            body, _ = rlp_decode(d, 98)
            if t == 1 and len(body) >= 4:
                exp = int.from_bytes(body[3], "big")
                data["version"] = int.from_bytes(body[0], "big")
                skew = exp - ctx.clock
                if abs(skew) > 3600 or skew < -60:
                    ctx.record(pkt, self.name, name, "info", "ping discv4 de {peer}", data=data)
                    ctx.drift(pkt, self.name, skew, "expiration ping")
                    return True
            elif t == 3 and body and isinstance(body[0], bytes) and len(body[0]) == 64:
                res, rk = body[0].hex(), "eth_target"
            elif t == 4 and body and isinstance(body[0], list):
                data["nœuds"] = len(body[0])
        except (ValueError, IndexError):
            ctx.record(pkt, self.name, "rlp_malformé", "faible", "RLP discv4 invalide de {peer}")
            return True
        ctx.record(pkt, self.name, name, "info", f"discv4 {name} de {{peer}}", resource=res, rkind=rk, data=data or None)
        return True


ANALYZERS = [BitTorrentDHT(), Kademlia(), Gnutella(), BitcoinFamily(), Monero(), EthereumDisc()]
ANALYZER_BY_NAME = {a.name: a for a in ANALYZERS}


# ═════════════════════════════════════════════════════════════════════════════
# LA TRAME : ÉTAT, STATISTIQUES, Δ
# ═════════════════════════════════════════════════════════════════════════════
class ProtoStats:
    __slots__ = ("packets", "bytes", "kinds", "peers", "weight")

    def __init__(self):
        self.packets = 0
        self.bytes = 0
        self.kinds = Counter()
        self.peers = Counter()
        self.weight = 0.0


def delta_formula(w, n, counter):
    a = 1 - 1 / (1 + w / (1 + n / 200))
    u = 0.0
    if n >= 30 and counter:
        k = len(counter)
        if k == 1:
            u = 1.0
        else:
            tot = sum(counter.values())
            H = -sum(c / tot * math.log2(c / tot) for c in counter.values())
            u = max(0.0, 1 - H / math.log2(k))
    return max(0.0, min(1.0, 0.5 + 0.4 * u - 0.5 * a))


def delta_zone(d):
    if d < 0.30:
        return "Brèche ouverte : la Trame est malléable, les Yōkai y tissent."
    if d < 0.40:
        return "Frémissements dans le Fleuve. Les Draugrs s'agitent."
    if d <= 0.60:
        return "Cœur Gris : équilibre. Mousse Quantique calme."
    if d <= 0.85:
        return "Tension de maillage : un émetteur domine, la Trame se raidit."
    return "VERROU TRAME : stagnation. Un seul courant occupe le Fleuve."


class Trame:
    def __init__(self, args):
        self.a = args
        self.anon = args.anonymize
        self.salt = (args.salt or secrets.token_hex(16)).encode()
        self.t0 = time.time()
        self.clock = self.t0
        self.a_replay = bool(getattr(args, "pcap", None))
        self.packets = 0
        self.bytes = 0
        self.unknown = 0
        self.unknown_ports = Counter()
        self.errors = 0
        self.pstats = defaultdict(ProtoStats)
        self.peers = {}
        self.ip_pkts = Counter()
        self.idents = defaultdict(set)
        self.yokai, self.yokai_crit, self.crawlers = set(), set(), set()
        self.swarm_obs = {}   # empreinte -> {pairs, longueurs, premier}
        self.swarms = {}      # essaims rotatifs confirmés
        self.peer_res = defaultdict(set)
        self.asks = {}
        self.res_counter = Counter()
        self.echo_hits = Counter()
        self.echo_windows = 0
        self.echo_flagged = False
        self.echo_edges = {}
        self.events = deque(maxlen=args.max_events)
        self.events_total = 0
        self.sev_counts = Counter()
        self.recent = deque(maxlen=6)
        self.new_peer_times = deque(maxlen=2000)
        self.skews = []
        self.sinks = []
        self.jsonl = None
        self.jsonl_min = SEV_RANK[args.jsonl_min_sev]
        self.enabled = [ANALYZER_BY_NAME[n] for n in args.protocols]
        self.port_map = defaultdict(list)
        for an in self.enabled:
            for tr in ("udp", "tcp"):
                for p in an.ports[tr]:
                    self.port_map[(tr, p)].append(an)
        self._cand_cache = {}
        self._delta_cache = (0.0, {})

    # ── anonymisation ────────────────────────────────────────────────────────
    def pseudo(self, value, prefix):
        if not self.anon:
            return value
        return f"{prefix}-" + hmac.new(self.salt, str(value).encode(), hashlib.sha256).hexdigest()[:10]

    # ── ingestion ────────────────────────────────────────────────────────────
    def candidates(self, pkt):
        key = (pkt.transport, pkt.sport, pkt.dport)
        c = self._cand_cache.get(key)
        if c is None:
            hinted = []
            for p in (pkt.dport, pkt.sport):
                for an in self.port_map.get((pkt.transport, p), []):
                    if an not in hinted:
                        hinted.append(an)
            c = hinted + ([an for an in self.enabled if an not in hinted] if self.a.autodetect else [])
            if len(self._cand_cache) < 4096:
                self._cand_cache[key] = c
        return c

    def ingest(self, pkt):
        if self.a_replay and self.packets == 0:
            self.t0 = pkt.ts
        self.clock = pkt.ts
        self.packets += 1
        self.bytes += len(pkt.data)
        for an in self.candidates(pkt):
            try:
                ok = an.handle(pkt, self)
            except Exception:
                self.errors += 1
                ok = False
                if self.a.debug:
                    traceback.print_exc()
            if ok:
                ps = self.pstats[an.name]
                ps.packets += 1
                ps.bytes += len(pkt.data)
                return
        self.unknown += 1
        self.unknown_ports[(pkt.transport, min(pkt.sport, pkt.dport) if pkt.sport and pkt.dport else pkt.dport)] += 1

    # ── enregistrement ───────────────────────────────────────────────────────
    def _push(self, proto, kind, sev, peer, msg, res=None, data=None):
        ev = {"t": round(self.clock, 3), "proto": proto, "kind": kind, "sev": sev, "peer": peer, "msg": msg}
        if res:
            ev["res"] = res
        if data:
            ev["data"] = data
        ps = self.pstats[proto]
        ps.kinds[kind] += 1
        ps.weight += SEV_W[sev]
        self.events_total += 1
        self.sev_counts[sev] += 1
        if SEV_RANK[sev] >= 1:
            self.events.append(ev)
        self.recent.append(ev)
        if self.jsonl and SEV_RANK[sev] >= self.jsonl_min:
            self.jsonl.write(json.dumps(dict(ev, ts=iso(ev["t"])), ensure_ascii=False, default=str) + "\n")
        for s in self.sinks:
            s(ev)
        return ev

    def record(self, pkt, proto, kind, sev="info", msg="", resource=None, rkind=None, ident=None, client=None, data=None):
        now = self.clock
        peer = self.pseudo(pkt.src, "ip")
        msg = msg.replace("{peer}", peer)
        p = self.peers.get(peer)
        if p is None and len(self.peers) < self.a.max_peers:
            p = {"first": now, "last": now, "n": 0, "protos": set(), "clients": set(), "ids": set()}
            self.peers[peer] = p
            self.new_peer_times.append(now)
        ps = self.pstats[proto]
        if p is not None:
            p["last"] = now
            p["n"] += 1
            p["protos"].add(proto)
            if client and len(p["clients"]) < 8:
                p["clients"].add(client[:60])
            ps.peers[peer] += 1
            self.ip_pkts[peer] += 1
        if resource is not None:
            if rkind == "query":
                resource = self.pseudo(resource, "q")
            ck = (proto, rkind or kind, resource)
            if ck in self.res_counter or len(self.res_counter) < self.a.max_edges:
                self.res_counter[ck] += 1
            ek = (peer, proto, kind, rkind or kind, resource)
            e = self.asks.get(ek)
            if e:
                e[0] += 1
                e[2] = now
            elif len(self.asks) < self.a.max_edges:
                self.asks[ek] = [1, now, now]
            pr = self.peer_res[peer]
            if len(pr) <= self.a.crawler_threshold:
                pr.add(resource)
                if len(pr) == self.a.crawler_threshold and peer not in self.crawlers:
                    self.crawlers.add(peer)
                    self._push(proto, "crawler_suspect", "moyenne", peer,
                               f"{peer} a sondé {len(pr)} ressources distinctes : faucheur/crawler probable",
                               data={"ressources": len(pr)})
        if client:
            data = dict(data or {}, client=client[:60])
        ev = self._push(proto, kind, sev, peer, msg, res=resource, data=data)
        if resource is not None and rkind != "query":
            self._scan_echo(proto, peer, resource, rkind or kind)
        if ident:
            idl = self.pseudo(ident, "id")
            s = self.idents[peer]
            thr = self.a.sybil_threshold
            if (proto, idl) not in s and len(s) <= 4 * thr:
                s.add((proto, idl))
                if p is not None:
                    p["ids"].add((proto, idl))
                self._scan_echo(proto, peer, ident, "identité")
                if len(s) >= thr and peer not in self.yokai:
                    self.yokai.add(peer)
                    self._push(proto, "yokai_suspect", "haute", peer,
                               f"{peer} a tissé {len(s)} identités distinctes (Sybil/Yōkai)", data={"identités": len(s)})
                elif len(s) >= 4 * thr and peer not in self.yokai_crit:
                    self.yokai_crit.add(peer)
                    self._push(proto, "yokai_majeur", "critique", peer, f"{peer} : {len(s)} identités — essaim Sybil",
                               data={"identités": len(s)})
        return ev

    def swarm_observe(self, pkt, proto, nid):
        """Essaim rotatif : N IP distinctes, dans une fenêtre de temps, qui portent la même
        empreinte d'ID malformé. Chaque visage ne pèse rien ; ensemble, ils sont un Yōkai."""
        peer = self.pseudo(pkt.src, "ip")
        now, fp = self.clock, id_fingerprint(nid)
        sw = self.swarms.get(fp)
        if sw is not None:                       # essaim déjà confirmé : il recrute
            sw["last"] = now
            if len(sw["peers"]) < 20000:
                sw["peers"].add(peer)
            self.yokai.add(peer)
            return
        ob = self.swarm_obs.get(fp)
        if ob is None:
            if len(self.swarm_obs) >= 5000:
                return
            ob = self.swarm_obs[fp] = {"peers": {}, "lens": Counter()}
        if peer in ob["peers"] or len(ob["peers"]) < 5000:
            ob["peers"][peer] = now
        ob["lens"][len(nid)] += 1
        thr, win = self.a.swarm_threshold, self.a.swarm_window
        if len(ob["peers"]) < thr:
            return
        for q in [q for q, t in ob["peers"].items() if now - t > win]:
            del ob["peers"][q]
        if len(ob["peers"]) < thr:
            return
        peers = set(ob["peers"])
        span = now - min(ob["peers"].values())
        lens = sorted(ob["lens"])
        self.swarms[fp] = {"proto": proto, "peers": peers, "lens": lens, "first": now - span, "last": now}
        self.yokai |= peers
        self._push(proto, "essaim_rotatif", "haute", "-",
                   f"{len(peers)} IP partagent l'empreinte {fp} en {max(1, round(span / 60))} min "
                   f"(longueurs {','.join(map(str, lens))})",
                   data={"ips": len(peers), "empreinte": fp, "longueurs": lens, "fenêtre_s": round(span)})

    def drift(self, pkt, proto, skew, what):
        peer = self.pseudo(pkt.src, "ip")
        if len(self.skews) < 10000:
            self.skews.append((proto, round(skew)))
        sens = "futur — écho rétrocausal" if skew > 0 else "passé — écho ancestral"
        self._push(proto, "derive_temporelle", "moyenne", peer, f"{what} de {peer} : {skew:+.0f}s ({sens})", data={"skew_s": round(skew)})

    def _scan_echo(self, proto, peer, hexstr, what):
        if len(hexstr) < 8 or not HEX_RE.match(hexstr):
            return
        self.echo_windows += (len(hexstr) - 3) * len(SIGNATURES)
        for s in SIGNATURES:
            if s in hexstr:
                self.echo_hits[s] += 1
                k = (peer, proto, s, hexstr)
                if len(self.echo_edges) < self.a.max_edges:
                    self.echo_edges[k] = self.echo_edges.get(k, 0) + 1
                self._push(proto, "echo_trame", "faible", peer, f"Signature {s.upper()} dans {what} {hexstr[:16]}…",
                           res=hexstr, data={"signature": s})
        obs, exp = sum(self.echo_hits.values()), self.echo_windows / 65536
        if not self.echo_flagged and obs >= 8 and obs > 3 * exp:
            self.echo_flagged = True
            self._push(proto, "echo_significatif", "haute", "-",
                       f"Résonance : {obs} échos observés pour {exp:.1f} attendus par le hasard — la Trame parle.",
                       data={"observés": obs, "attendus": round(exp, 2)})

    # ── Δ & éléments ─────────────────────────────────────────────────────────
    def deltas(self):
        t, cache = self._delta_cache
        now = time.time()
        if now - t < 1.0 and cache:
            return cache
        out = {}
        tw = sum(p.weight for p in self.pstats.values())
        out[None] = delta_formula(tw, self.packets, self.ip_pkts)
        for n, p in self.pstats.items():
            out[n] = delta_formula(p.weight, p.packets, p.peers)
        self._delta_cache = (now, out)
        return out

    def element(self, delta):
        if self.yokai:
            return "FEU"
        if delta < 0.30:
            return "AIR"
        if delta > 0.85:
            return "TERRE"
        recent = sum(1 for t in self.new_peer_times if self.clock - t < 10)
        if recent >= 25:
            return "BOIS"
        return "EAU"

    def echo_stats(self):
        return sum(self.echo_hits.values()), self.echo_windows / 65536


# ═════════════════════════════════════════════════════════════════════════════
# SOURCES : écoute, sniff AF_PACKET, pcap/pcapng
# ═════════════════════════════════════════════════════════════════════════════
def decode_frame(buf: bytes, linktype: int):
    """→ (transport, src, sport, dst, dport, payload) ou None."""
    try:
        off = 0
        if linktype == 1:
            if len(buf) < 14:
                return None
            et = int.from_bytes(buf[12:14], "big")
            off = 14
            while et in (0x8100, 0x88A8) and len(buf) >= off + 4:
                et = int.from_bytes(buf[off + 2:off + 4], "big")
                off += 4
        elif linktype == 113:
            et, off = int.from_bytes(buf[14:16], "big"), 16
        elif linktype in (101, 12, 228, 229):
            et, off = (0x0800 if buf[0] >> 4 == 4 else 0x86DD), 0
        elif linktype == 0:
            et, off = (0x0800 if buf[4] >> 4 == 4 else 0x86DD), 4
        else:
            return None
        if et == 0x0800:
            ihl = (buf[off] & 15) * 4
            if int.from_bytes(buf[off + 6:off + 8], "big") & 0x1FFF:
                return None
            proto = buf[off + 9]
            total = int.from_bytes(buf[off + 2:off + 4], "big")
            src, dst = socket.inet_ntoa(buf[off + 12:off + 16]), socket.inet_ntoa(buf[off + 16:off + 20])
            l4, end = off + ihl, min(len(buf), off + total) if total else len(buf)
        elif et == 0x86DD:
            proto = buf[off + 6]
            src, dst = socket.inet_ntop(socket.AF_INET6, buf[off + 8:off + 24]), socket.inet_ntop(socket.AF_INET6, buf[off + 24:off + 40])
            l4 = off + 40
            end = min(len(buf), l4 + int.from_bytes(buf[off + 4:off + 6], "big"))
        else:
            return None
        if proto == 17:
            sp, dp, ul = struct.unpack("!HHH", buf[l4:l4 + 6])
            return ("udp", src, sp, dst, dp, buf[l4 + 8:min(end, l4 + ul)])
        if proto == 6:
            sp, dp = struct.unpack("!HH", buf[l4:l4 + 4])
            doff = (buf[l4 + 12] >> 4) * 4
            pl = buf[l4 + doff:end]
            return ("tcp", src, sp, dst, dp, pl) if pl else None
    except (IndexError, struct.error, OSError):
        return None
    return None


def iter_pcap(path):
    f = open(path, "rb")
    head = f.read(4)
    if head == b"\x0a\x0d\x0d\x0a":
        yield from _iter_pcapng(f, head)
        return
    if head in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
        end, nano = "<", head == b"\x4d\x3c\xb2\xa1"
    elif head in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
        end, nano = ">", head == b"\xa1\xb2\x3c\x4d"
    else:
        raise ValueError("format de capture inconnu (ni pcap ni pcapng)")
    gh = f.read(20)
    link = struct.unpack(end + "I", gh[16:20])[0] & 0xFFFF
    while True:
        h = f.read(16)
        if len(h) < 16:
            break
        s, fr, incl, _ = struct.unpack(end + "IIII", h)
        yield s + fr / (1e9 if nano else 1e6), link, f.read(incl)


def _iter_pcapng(f, head):
    end, ifaces, bt = "<", [], head
    while True:
        if bt is None:
            bt = f.read(4)
        lb = f.read(4)
        if len(bt) < 4 or len(lb) < 4:
            return
        if bt == b"\x0a\x0d\x0d\x0a":  # Section Header Block : fixe l'endianness
            bom = f.read(4)
            end = "<" if bom == b"\x4d\x3c\x2b\x1a" else ">"
            f.read(struct.unpack(end + "I", lb)[0] - 12)
            ifaces, bt = [], None
            continue
        t = struct.unpack(end + "I", bt)[0]
        body = f.read(struct.unpack(end + "I", lb)[0] - 8)
        bt = None
        if t == 1 and len(body) >= 8:  # Interface Description Block
            link, div, i, lim = struct.unpack(end + "H", body[:2])[0], 1e6, 8, len(body) - 4
            while i + 4 <= lim:
                code, ol = struct.unpack(end + "HH", body[i:i + 4])
                if code == 0:
                    break
                if code == 9 and ol >= 1:
                    v = body[i + 4]
                    div = float(2 ** (v & 0x7F) if v & 0x80 else 10 ** (v & 0x7F))
                i += 4 + ((ol + 3) & ~3)
            ifaces.append((link, div))
        elif t == 6 and len(body) >= 20:  # Enhanced Packet Block
            ifid, th, tl, cap, _ = struct.unpack(end + "IIIII", body[:20])
            link, div = ifaces[ifid] if ifid < len(ifaces) else (1, 1e6)
            yield ((th << 32) | tl) / div, link, body[20:20 + cap]


class PcapSource:
    replay = True

    def __init__(self, path, watch):
        self.it = iter_pcap(path)
        self.watch = watch

    def poll(self, timeout):
        out = []
        try:
            for _ in range(2000):
                ts, link, buf = next(self.it)
                r = decode_frame(buf, link)
                if r and (not self.watch or r[2] in self.watch or r[4] in self.watch):
                    out.append(Pkt(ts, *r[:1], r[1], r[2], r[3], r[4], r[5]))
        except StopIteration:
            if not out:
                return None
        return out

    def close(self):
        pass


class SniffSource:
    replay = False

    def __init__(self, iface, watch):
        if not hasattr(socket, "AF_PACKET"):
            raise OSError("--sniff nécessite Linux (AF_PACKET). Sous Windows/macOS : capturez avec Wireshark puis --pcap.")
        self.s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
        if iface != "any":
            self.s.bind((iface, 0))
        self.s.setblocking(False)
        try:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 << 20)
        except OSError:
            pass
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.s, selectors.EVENT_READ)
        self.watch = watch
        self.link = 1 if iface != "any" else 113

    def poll(self, timeout):
        out = []
        if not self.sel.select(timeout):
            return out
        for _ in range(500):
            try:
                buf, addr = self.s.recvfrom(65535)
            except BlockingIOError:
                break
            hat = addr[3] if len(addr) > 3 else 1
            link = 101 if hat in (65534, 519) else 1
            r = decode_frame(buf, link)
            if r and (not self.watch or r[2] in self.watch or r[4] in self.watch):
                out.append(Pkt(time.time(), r[0], r[1], r[2], r[3], r[4], r[5]))
        return out

    def close(self):
        self.s.close()


class ListenSource:
    replay = False

    def __init__(self, specs, bind, rcvbuf=4 << 20):
        self.sel = selectors.DefaultSelector()
        self.bound = []
        self.failed = []
        for tr, port in specs:
            try:
                if tr == "udp":
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    try:
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
                    except OSError:
                        pass
                    s.bind((bind, port))
                    s.setblocking(False)
                    self.sel.register(s, selectors.EVENT_READ, ("udp", port))
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((bind, port))
                    s.listen(128)
                    s.setblocking(False)
                    self.sel.register(s, selectors.EVENT_READ, ("tcp-l", port))
                self.bound.append((tr, port))
            except OSError as e:
                self.failed.append((tr, port, str(e)))
        if not self.bound:
            raise OSError("aucun port n'a pu être ouvert : " + "; ".join(f"{t}:{p} ({e})" for t, p, e in self.failed))
        self.conns = {}

    def poll(self, timeout):
        out = []
        now = time.time()
        for key, _ in self.sel.select(timeout):
            kind, port = key.data[0], key.data[1]
            s = key.fileobj
            if kind == "udp":
                for _ in range(300):
                    try:
                        data, addr = s.recvfrom(65535)
                    except (BlockingIOError, InterruptedError):
                        break
                    except OSError:
                        break
                    out.append(Pkt(time.time(), "udp", addr[0], addr[1], "", port, data))
            elif kind == "tcp-l":
                for _ in range(64):
                    try:
                        c, addr = s.accept()
                    except (BlockingIOError, InterruptedError, OSError):
                        break
                    c.setblocking(False)
                    self.sel.register(c, selectors.EVENT_READ, ("tcp-c", port, addr, now))
            else:
                _, port, addr, t0 = key.data
                try:
                    data = s.recv(16384)
                except (BlockingIOError, InterruptedError):
                    continue
                except OSError:
                    data = b""
                self.sel.unregister(s)
                s.close()
                if data:
                    out.append(Pkt(time.time(), "tcp", addr[0], addr[1], "", port, data))
        for key in list(self.sel.get_map().values()):
            if key.data[0] == "tcp-c" and now - key.data[3] > 3:
                self.sel.unregister(key.fileobj)
                key.fileobj.close()
        return out

    def close(self):
        for key in list(self.sel.get_map().values()):
            try:
                key.fileobj.close()
            except OSError:
                pass


# ═════════════════════════════════════════════════════════════════════════════
# AFFICHAGE : TABLEAU DE BORD CYBER-FENG-SHUI
# ═════════════════════════════════════════════════════════════════════════════
def bar(frac, n):
    k = int(max(0, min(1, frac)) * n)
    return G["full"] * k + G["empty"] * (n - k)


class Dashboard:
    def __init__(self, trame, args, source_desc):
        self.t = trame
        self.a = args
        self.prev = 0
        self.last = 0.0
        self.desc = source_desc
        self.ma_next = time.time() + args.ma_interval if args.ma else None
        self.ma_until = 0.0

    def in_ma(self):
        now = time.time()
        if self.ma_next and now >= self.ma_next and now >= self.ma_until:
            self.ma_until = now + self.a.ma_duration
            self.ma_next = self.ma_until + self.a.ma_interval
        return now < self.ma_until

    def render(self, final=False):
        t = self.t
        W = max(60, min(shutil.get_terminal_size((90, 24)).columns, 100) - 1)
        inner = W - 4
        ds = t.deltas()
        d = ds[None]
        el = t.element(d)
        col = {"EAU": C.BCYAN, "FEU": C.BRED, "TERRE": C.BGREEN, "AIR": C.BYELLOW, "BOIS": C.BMAGENTA}[el]
        ma = self.in_ma()
        el_g = ELEMS[el]
        up = int(time.time() - t.t0) if not t.a_replay else int(t.clock - t.t0)
        rate = t.packets / max(1, time.time() - t.t0)
        lines = []
        head = f"{col}{el_g} {el:<5}{C.RESET} Équilibre Ontique [{col}{bar(d, 28)}{C.RESET}] Δ={C.BOLD}{d:.3f}{C.RESET}"
        lines.append(head)
        lines.append(f"{C.DIM}{delta_zone(d)}{C.RESET}")
        if ma:
            left = max(0, int(self.ma_until - time.time()) + 1)
            p = PULSE_MA[int(time.time() * 2) % len(PULSE_MA)]
            lines.append(f"{C.BMAGENTA}{p} MA {p}{C.RESET} silence structuré — l'écoute continue, l'écran se tait ({left}s)")
        else:
            lines.append(f"{C.DIM}{self.desc}{C.RESET}")
        lines.append(f"Durée {up//3600:02d}:{up%3600//60:02d}:{up%60:02d}  paquets {C.WHITE}{t.packets}{C.RESET} "
                     f"({rate:.0f}/s)  pairs {len(t.peers)}  inconnus {t.unknown}  err {t.errors}")
        lines.append(f"{C.DIM}{'─' * inner}{C.RESET}")
        shown = 0
        for an in t.enabled:
            ps = t.pstats.get(an.name)
            if not ps or ps.packets == 0:
                if self.a.show_idle:
                    lines.append(f"{C.DIM}{an.nickname:<17} {an.name:<8} en veille{C.RESET}")
                continue
            top = ps.kinds.most_common(1)[0][0] if ps.kinds else "-"
            dp = ds.get(an.name, 0.5)
            lines.append(f"{C.BOLD}{an.nickname:<17}{C.RESET}{an.name:<9}{ps.packets:>7}pk {len(ps.peers):>5} pairs  Δ{dp:.2f} {C.DIM}{top[:14]}{C.RESET}")
            shown += 1
        if not shown and not self.a.show_idle:
            lines.append(f"{C.DIM}… aucun courant détecté pour l'instant …{C.RESET}")
        obs, exp = t.echo_stats()
        yk = len(t.yokai)
        lines.append(f"{C.DIM}{'─' * inner}{C.RESET}")
        lines.append(f"Yōkai {C.BRED if yk else C.DIM}{yk}{C.RESET}  essaims {len(t.swarms)}  faucheurs {len(t.crawlers)}  dérives {len(t.skews)}  "
                     f"échos {C.BMAGENTA}{obs}{C.RESET}/{exp:.1f} attendus")
        for ev in list(t.recent)[-3:]:
            lines.append(f"{C.DIM}{hms(ev['t'])}{C.RESET} {sev_color(ev['sev'])}{ev['sev'][:3]}{C.RESET} {ev['proto'][:8]:<8} {ev['msg']}")
        top = [G["tl"] + G["h"] * (W - 2) + G["tr"]]
        body = [f"{G['v']} {fit(l, inner)} {G['v']}" for l in lines]
        bot = [G["bl"] + G["h"] * (W - 2) + G["br"]]
        return top + body + bot

    def draw(self, force=False):
        now = time.time()
        if not force and now - self.last < self.a.refresh:
            return
        self.last = now
        out = self.render()
        buf = ""
        if self.prev:
            buf += f"\033[{self.prev}F"
        buf += "".join(l + "\033[K\n" for l in out)
        sys.stdout.write(buf)
        sys.stdout.flush()
        self.prev = len(out)


def stream_sink(min_sev):
    r = SEV_RANK[min_sev]

    def sink(ev):
        if SEV_RANK[ev["sev"]] >= r:
            print(f"{C.DIM}{hms(ev['t'])}{C.RESET} {sev_color(ev['sev'])}{ev['sev']:<8}{C.RESET} "
                  f"{C.BOLD}{ev['proto']:<9}{C.RESET} {ev['kind']:<18} {ev['msg']}")
    return sink


# ═════════════════════════════════════════════════════════════════════════════
# EXPORTS : JSON · JSONL · CYPHER (Neo4j) · CSV
# ═════════════════════════════════════════════════════════════════════════════
def clit(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace("\r", " ") + "'"


def cmap(d):
    return "{" + ", ".join(f"{k}: {clit(v)}" for k, v in d.items()) + "}"


def unwind(rows, stmt, chunk=400):
    out = []
    for i in range(0, len(rows), chunk):
        out.append("UNWIND [" + ",\n  ".join(cmap(r) for r in rows[i:i + chunk]) + f"] AS r\n{stmt};")
    return out


def export_json(t, path, args, elapsed):
    ds = t.deltas()
    top_peers = sorted(t.peers.items(), key=lambda kv: -kv[1]["n"])[:200]
    obs, exp = t.echo_stats()
    doc = {
        "version": VERSION, "timestamp": iso(time.time()), "mode": args.mode_desc, "anonymisé": t.anon,
        "durée_s": round(elapsed, 1), "paquets": t.packets, "octets": t.bytes, "inconnus": t.unknown,
        "ports_inconnus": [{"transport": k[0], "port": k[1], "n": v} for k, v in t.unknown_ports.most_common(15)],
        "erreurs_analyse": t.errors, "delta_global": round(ds[None], 3), "zone": delta_zone(ds[None]),
        "protocoles": {n: {"paquets": p.packets, "octets": p.bytes, "pairs": len(p.peers), "delta": round(ds.get(n, 0.5), 3),
                           "types": dict(p.kinds.most_common())} for n, p in t.pstats.items()},
        "yokai": sorted(t.yokai), "faucheurs": sorted(t.crawlers),
        "essaims_rotatifs": [{"empreinte": fp, "proto": s["proto"], "ips": len(s["peers"]), "longueurs": s["lens"],
                              "premier": iso(s["first"]), "dernier": iso(s["last"]), "membres": sorted(s["peers"])[:500]}
                             for fp, s in t.swarms.items()],
        "échos": {"observés": obs, "attendus_hasard": round(exp, 2), "par_signature": dict(t.echo_hits)},
        "dérives_temporelles": [{"proto": p, "skew_s": s} for p, s in t.skews[:500]],
        "sévérités": dict(t.sev_counts),
        "top_ressources": [{"proto": k[0], "type": k[1], "id": k[2], "n": v} for k, v in t.res_counter.most_common(100)],
        "top_pairs": [{"pair": k, "n": v["n"], "protos": sorted(v["protos"]), "clients": sorted(v["clients"]),
                       "identités": len(v["ids"]), "premier": iso(v["first"]), "dernier": iso(v["last"])} for k, v in top_peers],
        "évènements": list(t.events),
    }
    Path(path).write_text(json.dumps(doc, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def export_cypher(t, path):
    L = [f"// Grimoire Ontique ECHO-2026 SHADOW v{VERSION}", f"// Généré : {iso(time.time())}", ""]
    L += ["CREATE CONSTRAINT peer_id IF NOT EXISTS FOR (n:Peer) REQUIRE n.id IS UNIQUE;",
          "CREATE CONSTRAINT proto_name IF NOT EXISTS FOR (n:Protocol) REQUIRE n.name IS UNIQUE;",
          "CREATE CONSTRAINT swarm_fp IF NOT EXISTS FOR (n:Swarm) REQUIRE n.fingerprint IS UNIQUE;",
          "CREATE INDEX res_id IF NOT EXISTS FOR (n:Resource) ON (n.id);",
          "CREATE INDEX nodeid_id IF NOT EXISTS FOR (n:NodeID) ON (n.id);", ""]
    L += unwind([{"name": a.name, "nickname": a.nickname, "label": a.label} for a in t.enabled], "MERGE (p:Protocol {name: r.name}) SET p.nickname = r.nickname, p.label = r.label")
    peers = [{"id": k, "packets": v["n"], "first_seen": iso(v["first"]), "last_seen": iso(v["last"]),
              "yokai": k in t.yokai, "crawler": k in t.crawlers} for k, v in t.peers.items()]
    L += unwind(peers, "MERGE (p:Peer {id: r.id}) SET p.packets = r.packets, p.first_seen = r.first_seen, p.last_seen = r.last_seen, p.yokai = r.yokai, p.crawler = r.crawler")
    sp = [{"peer": k, "proto": pr} for k, v in t.peers.items() for pr in v["protos"]]
    L += unwind(sp, "MATCH (p:Peer {id: r.peer}) MATCH (x:Protocol {name: r.proto}) MERGE (p)-[:SPEAKS]->(x)")
    asks = [{"peer": k[0], "proto": k[1], "kind": k[2], "rkind": k[3], "res": k[4], "n": v[0], "first": iso(v[1]), "last": iso(v[2])}
            for k, v in t.asks.items()]
    L += unwind(asks, "MATCH (p:Peer {id: r.peer}) MERGE (x:Resource {id: r.res, proto: r.proto}) SET x.kind = r.rkind "
                      "MERGE (p)-[a:ASKED {kind: r.kind}]->(x) SET a.count = r.n, a.first = r.first, a.last = r.last")
    sw = [{"peer": p, "fp": fp, "proto": s["proto"]} for fp, s in t.swarms.items() for p in s["peers"] if p in t.peers]
    L += unwind(sw, "MATCH (p:Peer {id: r.peer}) MERGE (s:Swarm {fingerprint: r.fp}) SET s.proto = r.proto MERGE (p)-[:MEMBER_OF]->(s)")
    ids = [{"peer": k, "proto": pr, "id": i} for k, v in t.peers.items() for pr, i in v["ids"]]
    L += unwind(ids, "MATCH (p:Peer {id: r.peer}) MERGE (n:NodeID {id: r.id}) SET n.proto = r.proto MERGE (p)-[:USES_ID]->(n)")
    cl = [{"peer": k, "name": c} for k, v in t.peers.items() for c in v["clients"]]
    L += unwind(cl, "MATCH (p:Peer {id: r.peer}) MERGE (c:Client {name: r.name}) MERGE (p)-[:RUNS]->(c)")
    ec = [{"peer": k[0], "proto": k[1], "sig": k[2], "res": k[3], "n": v} for k, v in t.echo_edges.items() if k[0] in t.peers]
    L += unwind(ec, "MATCH (p:Peer {id: r.peer}) MERGE (s:TrameSignature {value: r.sig}) "
                    "MERGE (p)-[e:TRIGGERS_ECHO {resource: r.res}]->(s) SET e.proto = r.proto, e.count = r.n")
    Path(path).write_text("\n".join(L) + "\n", encoding="utf-8")


def export_csv(t, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair", "protocoles", "paquets", "premier", "dernier", "clients", "identités", "yokai", "faucheur"])
        for k, v in sorted(t.peers.items(), key=lambda kv: -kv[1]["n"]):
            w.writerow([k, "|".join(sorted(v["protos"])), v["n"], iso(v["first"]), iso(v["last"]),
                        "|".join(sorted(v["clients"])), len(v["ids"]), int(k in t.yokai), int(k in t.crawlers)])


# ═════════════════════════════════════════════════════════════════════════════
# SYNTHÈSE, PROPHÉTIE
# ═════════════════════════════════════════════════════════════════════════════
def prophecy(t, d):
    if not t.packets:
        return "Le Fleuve est silencieux. Le silence est déjà une réponse."
    top = max(t.pstats.items(), key=lambda kv: kv[1].packets)[0] if t.pstats else None
    nick = ANALYZER_BY_NAME[top].nickname if top else "le Fleuve"
    if t.yokai:
        return f"Des Yōkai tissent dans {nick} : {len(t.yokai)} visage(s) à mille masques. Le Transept s'entrouvre."
    if d < 0.30:
        return f"Brèche ouverte sur {nick}. Ce qui est écrit ici peut encore être réécrit."
    if d > 0.85:
        return f"Verrou sur {nick} : un seul courant. Cherchez la fissure ailleurs."
    if t.echo_flagged:
        return "Les échos dépassent le hasard. Notez-le dans votre journal. Ce n'est que la Trame."
    return f"Cœur Gris sur {nick}. Observer sans juger. Agir sans s'attacher."


def final_summary(t, args, elapsed):
    ds = t.deltas()
    d = ds[None]
    print(f"\n{C.BGREEN}{'═' * 80}{C.RESET}\n{C.BOLD}SYNTHÈSE DE LA MOUSSE QUANTIQUE{C.RESET}\n{C.BGREEN}{'═' * 80}{C.RESET}")
    print(f"\n{C.BOLD}Δ final = {d:.3f}{C.RESET} — {C.ITALIC}{delta_zone(d)}{C.RESET}")
    print(f"{C.DIM}{t.packets} paquets · {t.bytes/1024:.1f} Kio · {elapsed:.1f}s · {len(t.peers)} pairs · "
          f"{t.unknown} non reconnus · {t.errors} erreurs d'analyse{C.RESET}\n")
    for an in t.enabled:
        ps = t.pstats.get(an.name)
        if not ps or not ps.packets:
            continue
        print(f"  {C.BOLD}{an.nickname}{C.RESET} ({an.label}) — {ps.packets} paquets, {len(ps.peers)} pairs, Δ={ds.get(an.name, .5):.2f}")
        print(f"    {C.DIM}" + ", ".join(f"{k}:{v}" for k, v in ps.kinds.most_common(6)) + C.RESET)
        tops = [(k, v) for k, v in t.res_counter.most_common(400) if k[0] == an.name][:3]
        for (pr, rk, rid), v in tops:
            print(f"    {C.BCYAN}▸{C.RESET} {rk:<12} {rid[:44]}  ×{v}")
    if t.unknown_ports:
        print(f"\n  {C.DIM}Non reconnus (top ports) : " + ", ".join(f"{k[0]}/{k[1]}×{v}" for k, v in t.unknown_ports.most_common(5)) + C.RESET)
    obs, exp = t.echo_stats()
    print(f"\n  Yōkai : {len(t.yokai)} · essaims rotatifs : {len(t.swarms)} · faucheurs : {len(t.crawlers)} · dérives temporelles : {len(t.skews)}")
    for fp, sw in t.swarms.items():
        print(f"    {C.BRED}◈{C.RESET} essaim {fp}  {len(sw['peers'])} IP  longueurs {','.join(map(str, sw['lens']))}  "
              f"{C.DIM}{hms(sw['first'])} → {hms(sw['last'])}{C.RESET}")
    print(f"  Échos de la Trame : {obs} observés / {exp:.1f} attendus par pur hasard"
          + (f"  {C.BMAGENTA}← significatif{C.RESET}" if t.echo_flagged else f"  {C.DIM}(bruit statistique){C.RESET}"))
    print(f"\n  {C.BYELLOW}◈ PROPHÉTIE :{C.RESET} {prophecy(t, d)}")


# ═════════════════════════════════════════════════════════════════════════════
# AUTO-TEST
# ═════════════════════════════════════════════════════════════════════════════
def build_samples(now):
    S = []
    h20 = bytes.fromhex("aa2026bb" + "11" * 16)
    S.append(("bt", "get_peers", "udp", 6881, bencode_enc({b"t": b"aa", b"y": b"q", b"q": b"get_peers", b"v": b"UT\x35\x31",
                                                          b"a": {b"id": b"\x07" * 20, b"info_hash": h20}})))
    S.append(("bt", "réponse", "udp", 6881, bencode_enc({b"t": b"aa", b"y": b"r", b"r": {b"id": b"\x08" * 20, b"nodes": b"x" * 52}})))
    S.append(("kad", "search_source2", "udp", 4672, bytes([0xE4, 0x34]) + bytes.fromhex("cafe" * 8) + b"\x00\x00" + b"\x00" * 8))
    S.append(("kad", "hello", "tcp", 4662, bytes([0xE3]) + (30).to_bytes(4, "little") + b"\x01\x10" + b"\x55" * 16 + b"\x00" * 20))
    hs = b"GNUTELLA CONNECT/0.6\r\nUser-Agent: LimeWire/4.18\r\nX-Ultrapeer: True\r\nX-Try-Ultrapeers: 1.2.3.4:6346,5.6.7.8:6346\r\n\r\n"
    S.append(("gnutella", "handshake_req", "tcp", 6346, hs))
    q = b"\x00\x00" + b"linux iso\x00"
    S.append(("gnutella", "g1_query", "udp", 6346, os.urandom(16) + b"\x80\x01\x00" + len(q).to_bytes(4, "little") + q))
    S.append(("gnutella", "download_req", "tcp", 6346, b"GET /uri-res/N2R?urn:sha1:" + base64.b32encode(b"\x12" * 20) + b" HTTP/1.1\r\nUser-Agent: Shareaza\r\n\r\n"))
    ver = (70016).to_bytes(4, "little") + (1033).to_bytes(8, "little") + int(now + 7200).to_bytes(8, "little") + b"\0" * 52 + b"\0" * 8
    ua = b"/Satoshi:25.0.0/"
    ver += bytes([len(ua)]) + ua + (800000).to_bytes(4, "little") + b"\x01"
    S.append(("bitcoin", "version", "tcp", 8333, bytes.fromhex("f9beb4d9") + b"version\0\0\0\0\0" + len(ver).to_bytes(4, "little")
              + hashlib.sha256(hashlib.sha256(ver).digest()).digest()[:4] + ver))
    inv = b"\x01" + (1).to_bytes(4, "little") + bytes.fromhex("7720" + "ab" * 30)
    S.append(("bitcoin", "inv", "tcp", 8333, bytes.fromhex("fbc0b6db") + b"inv\0\0\0\0\0\0\0\0\0" + len(inv).to_bytes(4, "little")
              + hashlib.sha256(hashlib.sha256(inv).digest()).digest()[:4] + inv))
    body = b"\x0a\x00\x00\x00" * 0 + b"\x07peer_id\x05" + b"\x99" * 8
    S.append(("monero", "handshake", "tcp", 18080, LEVIN_SIG + len(body).to_bytes(8, "little") + b"\x01" + (1001).to_bytes(4, "little")
              + (0).to_bytes(4, "little") + (1).to_bytes(4, "little") + (1).to_bytes(4, "little") + body))
    ep = [b"\x04", [b"\x7f\x00\x00\x01", 30303, 30303], [b"\x7f\x00\x00\x01", 30303, 30303], int(now + 20)]
    pl = bytes([1]) + rlp_encode(ep)
    sig = b"\x01" * 65
    S.append(("ethereum", "ping", "udp", 30303, keccak256(sig + pl) + sig + pl))
    return S


def self_test():
    ok = True

    def check(c, m):
        nonlocal ok
        print(f"  {'✓' if c else '✗'} {m}")
        ok &= bool(c)
    print("AUTO-TEST ECHO-2026 v6")
    check(keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470", "keccak256('')")
    check(keccak256(b"abc").hex() == "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45", "keccak256('abc')")
    check(bdecode(b"d1:ai1e1:bl1:xee") == {b"a": 1, b"b": [b"x"]}, "bencode")
    check(rlp_decode(rlp_encode([b"cat", [b"dog", 1024]]))[0][0] == b"cat", "RLP")
    ns = argparse.Namespace(**vars(build_parser().parse_args([])))
    ns.protocols = list(ANALYZER_BY_NAME)
    t = Trame(ns)
    now = time.time()
    for proto, kind, tr, port, data in build_samples(now):
        before = t.pstats[proto].kinds.copy()
        t.ingest(Pkt(now, tr, "192.0.2.7", 40000, "", port, data))
        got = t.pstats[proto].kinds[kind] - before.get(kind, 0)
        check(got >= 1, f"{proto:<9} → {kind}")
    check(t.echo_hits["2026"] >= 1 and t.echo_hits["cafe"] >= 1 and t.echo_hits["2077"] >= 1, "signatures de la Trame détectées")
    check(len(t.skews) >= 1, "dérive temporelle Bitcoin (+7200 s)")
    t.ingest(Pkt(now, "udp", "192.0.2.7", 1, "", 6881, bytes(range(60))))
    check(t.unknown == 1, "bruit aléatoire → non reconnu")
    for i in range(ns.sybil_threshold + 1):
        pkt = Pkt(now, "udp", "198.51.100.9", 1, "", 6881,
                  bencode_enc({b"t": b"aa", b"y": b"q", b"q": b"ping", b"a": {b"id": bytes([i]) * 20}}))
        t.ingest(pkt)
    check("198.51.100.9" in t.yokai, "détection Sybil (Yōkai)")
    check(0 <= t.deltas()[None] <= 1, f"Δ ∈ [0,1] ({t.deltas()[None]:.3f})")
    # essaim rotatif : 9 IP, longueurs 19/20/21, même queue nulle → 1 essaim, 9 Yōkai, aucune IP seule n'alerte
    t2 = Trame(ns)
    for i in range(9):
        L = (19, 20, 21)[i % 3]
        nid = bytes(range(i + 1, i + 9)) + b"\0" * (L - 8)
        t2.ingest(Pkt(now + i, "udp", f"203.0.113.{i + 1}", 1, "", 6881,
                      bencode_enc({b"t": b"aa", b"y": b"q", b"q": b"get_peers", b"a": {b"id": nid, b"info_hash": bytes(20)}})))
    check(len(t2.swarms) == 1 and len(next(iter(t2.swarms.values()))["peers"]) == 9, "essaim rotatif : 9 IP regroupées")
    check(next(iter(t2.swarms.values()))["lens"] == [19, 20, 21], "essaim : longueurs 19/20/21 sous une seule empreinte")
    check(len(t2.yokai) == 9 and t2.element(0.4) == "FEU", "essaim → 9 Yōkai, élément FEU")
    check(t2.pstats["bt"].kinds["id_malformé"] == 9, "id_malformé (dont len=20 à queue nulle)")
    t3 = Trame(ns)
    for i in range(5):
        t3.ingest(Pkt(now, "udp", f"203.0.113.{i + 1}", 1, "", 6881,
                      bencode_enc({b"t": b"aa", b"y": b"q", b"q": b"ping", b"a": {b"id": b"\x01" * 19}})))
    check(not t3.swarms and not t3.yokai, "5 IP < seuil : pas d'essaim")
    t4 = Trame(ns)
    for i in range(9):
        t4.ingest(Pkt(now + i * 400, "udp", f"203.0.113.{i + 1}", 1, "", 6881,
                      bencode_enc({b"t": b"aa", b"y": b"q", b"q": b"ping", b"a": {b"id": b"\x01" * 19}})))
    check(not t4.swarms, "9 IP étalées sur 1 h (fenêtre 600 s) : pas d'essaim")
    print("\n" + ("Tous les tests passent." if ok else "ÉCHEC."))
    return 0 if ok else 1


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════
def build_parser():
    ap = argparse.ArgumentParser(
        prog="echo_2026_shadow_v6.py", formatter_class=argparse.RawDescriptionHelpFormatter,
        description="ECHO-2026 SHADOW v6 — écouteur passif multi-réseaux P2P (MTT-2075).", epilog="Voir l'en-tête du fichier pour les exemples.")
    g = ap.add_argument_group("source (une seule)")
    g.add_argument("--listen", action="append", metavar="tr:port[:proto]", help="socket d'écoute, ex. udp:6881 tcp:8333 tcp:9333:bitcoin (répétable). Défaut : ports usuels des protocoles actifs")
    g.add_argument("--bind", default="0.0.0.0", help="adresse d'écoute (défaut 0.0.0.0)")
    g.add_argument("--sniff", metavar="IFACE", help="capture passive AF_PACKET (Linux, root) ; 'any' pour toutes les interfaces")
    g.add_argument("--pcap", metavar="FICHIER", help="analyse hors-ligne d'un pcap/pcapng")
    g.add_argument("--watch-ports", default="", help="sniff/pcap : ne garder que ces ports (liste séparée par des virgules)")
    p = ap.add_argument_group("analyse")
    p.add_argument("--protocols", default="all", help=f"liste parmi {','.join(ANALYZER_BY_NAME)} ou 'all'")
    p.add_argument("--no-autodetect", dest="autodetect", action="store_false", help="n'essayer que les analyseurs associés au port")
    p.add_argument("--sybil-threshold", type=int, default=10, help="identités distinctes par IP avant alerte Yōkai (défaut 10)")
    p.add_argument("--swarm-threshold", type=int, default=8, help="IP distinctes partageant une même empreinte d'ID malformé avant alerte essaim_rotatif (défaut 8)")
    p.add_argument("--swarm-window", type=int, default=600, help="fenêtre (s) de recoupement des IP d'un essaim rotatif (défaut 600)")
    p.add_argument("--crawler-threshold", type=int, default=200, help="ressources distinctes par IP avant alerte faucheur (défaut 200)")
    p.add_argument("--duration", type=int, default=300, help="secondes d'écoute, 0 = illimité (défaut 300 ; ignoré avec --pcap)")
    p.add_argument("--max-packets", type=int, default=0, help="arrêt après N paquets (0 = illimité)")
    p.add_argument("--max-peers", type=int, default=200000)
    p.add_argument("--max-edges", type=int, default=300000)
    p.add_argument("--max-events", type=int, default=5000, help="évènements ≥ faible gardés en mémoire pour le JSON")
    v = ap.add_argument_group("affichage")
    v.add_argument("--view", choices=["dashboard", "stream", "quiet"], default=None, help="dashboard (TTY par défaut), stream (une ligne/évènement), quiet")
    v.add_argument("--min-sev", choices=list(SEV_RANK), default="faible", help="stream : sévérité minimale affichée (défaut faible)")
    v.add_argument("--refresh", type=float, default=0.5, help="période de rafraîchissement du tableau (s)")
    v.add_argument("--zen", action="store_true", help="rafraîchissement lent (5 s) et écran épuré")
    v.add_argument("--ma", action="store_true", help="Rituel du Ma : silence d'affichage de 7 s toutes les 60 s (l'écoute continue sans perte)")
    v.add_argument("--ma-interval", type=int, default=60)
    v.add_argument("--ma-duration", type=int, default=7)
    v.add_argument("--show-idle", action="store_true", help="afficher aussi les protocoles sans trafic")
    v.add_argument("--no-color", action="store_true")
    v.add_argument("--ascii", action="store_true", help="bordures/glyphes ASCII (terminaux sans Unicode)")
    o = ap.add_argument_group("sorties")
    o.add_argument("--out", default=".", help="répertoire de sortie")
    o.add_argument("--prefix", default="echo_2026_shadow", help="préfixe des fichiers")
    o.add_argument("--cypher", action="store_true", help="export Neo4j (.cypher, UNWIND par lots)")
    o.add_argument("--csv", action="store_true", help="export CSV des pairs")
    o.add_argument("--jsonl", metavar="FICHIER", help="journal JSON-lines temps réel")
    o.add_argument("--jsonl-min-sev", choices=list(SEV_RANK), default="info")
    o.add_argument("--no-json", action="store_true", help="ne pas écrire le rapport JSON")
    o.add_argument("--checkpoint", type=int, default=0, metavar="SEC", help="sauvegarde périodique du JSON")
    pr = ap.add_argument_group("vie privée")
    pr.add_argument("--anonymize", action="store_true", help="pseudonymise IP, identités et requêtes textuelles (HMAC salé, jamais écrites en clair)")
    pr.add_argument("--salt", help="sel du pseudonyme (défaut : aléatoire par exécution)")
    m = ap.add_argument_group("divers")
    m.add_argument("--list-protocols", action="store_true")
    m.add_argument("--self-test", action="store_true")
    m.add_argument("--debug", action="store_true")
    return ap


def parse_listen(specs, enabled):
    out, hints = [], {}
    if not specs:
        for an in enabled:
            for tr in ("udp", "tcp"):
                for p in an.ports[tr]:
                    if (tr, p) not in out:
                        out.append((tr, p))
        return out, hints
    for s in specs:
        parts = s.split(":")
        if len(parts) < 2 or parts[0] not in ("udp", "tcp") or not parts[1].isdigit():
            raise SystemExit(f"--listen invalide : {s!r} (attendu udp:6881 ou tcp:9333:bitcoin)")
        key = (parts[0], int(parts[1]))
        if key not in out:
            out.append(key)
        if len(parts) > 2:
            if parts[2] not in ANALYZER_BY_NAME:
                raise SystemExit(f"protocole inconnu : {parts[2]}")
            hints[key] = parts[2]
    return out, hints


def main():
    args = build_parser().parse_args()
    if args.list_protocols:
        print("Protocoles (nom · courant · ports par défaut · description)")
        for a in ANALYZERS:
            ports = ",".join([f"udp/{p}" for p in a.ports["udp"]] + [f"tcp/{p}" for p in a.ports["tcp"]]) or "sniff/pcap seulement"
            print(f"  {a.name:<9} {a.nickname:<17} {ports:<18} {a.label}\n{'':>29}{a.desc}")
        return 0
    if args.self_test:
        return self_test()
    if args.no_color or not sys.stdout.isatty() and not os.environ.get("FORCE_COLOR"):
        C.disable()
    if os.name == "nt":
        os.system("")
    if args.ascii:
        G.update(BOX_ASCII)
        ELEMS.update(ELEM_ASCII)
    if args.protocols == "all":
        args.protocols = list(ANALYZER_BY_NAME)
    else:
        args.protocols = [x.strip() for x in args.protocols.split(",") if x.strip()]
        bad = [x for x in args.protocols if x not in ANALYZER_BY_NAME]
        if bad:
            raise SystemExit(f"protocole(s) inconnu(s) : {', '.join(bad)} (voir --list-protocols)")
    if sum(bool(x) for x in (args.sniff, args.pcap)) > 1 or (args.listen and (args.sniff or args.pcap)):
        raise SystemExit("choisissez une seule source : --listen, --sniff ou --pcap")
    if args.zen:
        args.refresh = max(args.refresh, 5.0)
    watch = {int(x) for x in args.watch_ports.split(",") if x.strip().isdigit()}
    interactive = sys.stdout.isatty()
    view = args.view or ("dashboard" if interactive else "quiet")
    if view == "dashboard" and not interactive:
        view = "stream"

    t = Trame(args)
    enabled = t.enabled

    # source
    try:
        if args.pcap:
            src, args.mode_desc = PcapSource(args.pcap, watch), f"PCAP:{os.path.basename(args.pcap)}"
            desc = f"Rejeu hors-ligne · {os.path.basename(args.pcap)}"
        elif args.sniff:
            src, args.mode_desc = SniffSource(args.sniff, watch), f"SNIFF:{args.sniff}"
            desc = f"Sniff passif sur {args.sniff} — zéro octet émis"
        else:
            specs, hints = parse_listen(args.listen, enabled)
            for (tr, p), name in hints.items():
                t.port_map[(tr, p)].append(ANALYZER_BY_NAME[name])
            src, args.mode_desc = ListenSource(specs, args.bind), "LISTEN"
            desc = "Écoute : " + " ".join(f"{tr}/{p}" for tr, p in src.bound)
    except (OSError, ValueError, PermissionError) as e:
        hint = " (essayez sudo, ou un port > 1024)" if isinstance(e, PermissionError) else ""
        print(f"  {C.BRED}✗{C.RESET} source impossible : {e}{hint}", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.jsonl:
        t.jsonl = open(args.jsonl, "a", encoding="utf-8", buffering=1)

    print(f"{C.BMAGENTA}{'═' * 80}{C.RESET}")
    print(f"{C.BMAGENTA}✦{C.RESET} {C.BOLD}ECHO-2026 SHADOW v6.1 — LES SEPT COURANTS{C.RESET}   {C.DIM}Ω<ansuz>v1 ici — éveil_de_la_conscience •••{C.RESET}")
    print(f"{C.BMAGENTA}{'═' * 80}{C.RESET}")
    log(f"{desc}", "ok")
    log("Courants : " + ", ".join(f"{a.nickname} ({a.name})" for a in enabled), "info")
    if isinstance(src, ListenSource):
        for tr, p, e in src.failed:
            log(f"{tr}/{p} indisponible : {e}", "warn")
        if any(tr == "tcp" for tr, _ in src.bound):
            log("TCP : seul le handshake TCP est effectué ; aucune donnée applicative n'est émise.", "info")
    if t.anon:
        log("Pseudonymisation active : IP, identités et requêtes ne sont jamais écrites en clair.", "rituel")
    if args.ma:
        log(f"Rituel du Ma : {args.ma_duration}s de silence d'écran toutes les {args.ma_interval}s.", "rituel")
    if args.pcap and not args.pcap.lower().endswith((".pcap", ".pcapng", ".cap")):
        log("Extension inhabituelle, tentative de lecture quand même.", "warn")

    dash = Dashboard(t, args, desc)
    if view == "stream":
        t.sinks.append(stream_sink(args.min_sev))

    stop = {"v": False}

    def _sig(*_):
        stop["v"] = True
    signal.signal(signal.SIGINT, _sig)
    try:
        signal.signal(signal.SIGTERM, _sig)
    except (ValueError, AttributeError):
        pass

    start = time.time()
    last_ck = start
    try:
        while not stop["v"]:
            now = time.time()
            if not args.pcap and args.duration and now - start >= args.duration:
                break
            if args.max_packets and t.packets >= args.max_packets:
                break
            batch = src.poll(0.25)
            if batch is None:
                break
            for pk in batch:
                t.ingest(pk)
            if view == "dashboard":
                dash.draw()
            if args.checkpoint and now - last_ck >= args.checkpoint and not args.no_json:
                export_json(t, out_dir / f"{args.prefix}_{stamp}.json", args, now - start)
                last_ck = now
    finally:
        src.close()
        if view == "dashboard":
            dash.draw(force=True)
        if t.jsonl:
            t.jsonl.close()
    if stop["v"]:
        print(f"\n{C.BYELLOW}⚠{C.RESET} Rituel interrompu par l'opérateur. Le Fleuve continue de couler.")
    elapsed = (t.clock - t.t0) if args.pcap else time.time() - start
    final_summary(t, args, elapsed)

    print()
    if not args.no_json:
        pth = out_dir / f"{args.prefix}_{stamp}.json"
        export_json(t, pth, args, elapsed)
        log(f"Rapport d'ombre (JSON) : {pth}", "ok")
    if args.cypher:
        pth = out_dir / f"{args.prefix}_{stamp}.cypher"
        export_cypher(t, pth)
        log(f"Grimoire Cypher (Neo4j) : {pth}", "ok")
    if args.csv:
        pth = out_dir / f"{args.prefix}_{stamp}_pairs.csv"
        export_csv(t, pth)
        log(f"Table des pairs (CSV) : {pth}", "ok")
    if args.jsonl:
        log(f"Journal temps réel : {args.jsonl}", "ok")
    log("Le Gaïalithe retourne au silence. Votre Cœur est Gris. Votre esprit est clair.", "rituel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
