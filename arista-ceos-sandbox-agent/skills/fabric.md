# Skill: fabric

Help an operator see **whether the 3-node eBGP underlay is up**:
identity, BGP sessions, LLDP, interface state.

## Do this

1. Call `ceos_whoami` on each node if identity is not already known
   this turn. Confirm hostname and EOS version from eAPI, not from
   this markdown.
2. Call `ceos_bgp_summary`. Expected neighbors (design only — still
   read state from the tool):

   | Node | Neighbor | Remote AS |
   |------|----------|-----------|
   | spine1 | 10.0.1.1 | 65101 |
   | spine1 | 10.0.2.1 | 65102 |
   | leaf1 | 10.0.1.0 | 65000 |
   | leaf2 | 10.0.2.0 | 65000 |

   Report `peerState` as returned. If a peer is missing or not
   Established, say that. Do not write Established from the table
   above.
3. Call `ceos_lldp`. Design links: spine1 Ethernet1↔leaf1 Ethernet1,
   spine1 Ethernet2↔leaf2 Ethernet1.
4. Call `ceos_interfaces` if someone asks why a session is down
   (protocol/status, IPv4). Do not dump Management0 secrets.

## Do not

- Configure BGP, clear sessions, or shut interfaces.
- Assume leaf1 and leaf2 have a direct link (they do not).
- Print the eAPI password or a `username … secret` line.
- Talk about MPLS or EVPN as if they are configured in v1.

## How to say it

Lead with one sentence: “N of 2 spine–leaf BGP sessions Established
(as of tool time); LLDP sees ….” Then a short table. If eAPI is
unreachable, give the HTTP status or connect error, not a guessed
state.
