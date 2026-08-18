# Skill: routing

Help an operator see **whether loopbacks are in the underlay RIB**
and whether they ping.

## Do this

1. Call `ceos_whoami` if the node set is unclear.
2. Call `ceos_routes` (or equivalent `show ip route`) on the node
   the human named. Loopbacks in the design:

   | Prefix | Origin |
   |--------|--------|
   | 10.255.0.1/32 | spine1 Loopback0 |
   | 10.255.0.11/32 | leaf1 Loopback0 |
   | 10.255.0.12/32 | leaf2 Loopback0 |

   Say whether each prefix is **connected** or **BGP** on that node,
   using the tool output. A missing prefix is “not in RIB”, not
   “probably there.”
3. If asked “can A reach B?”, call `ceos_ping` (or refuse if the
   tool is missing) from the source node to the destination
   loopback. Quote packets received / loss from the result.
4. Point-to-point `/31`s (`10.0.1.0/31`, `10.0.2.0/31`) are the
   underlay hops. Do not invent a `10.0.3.0/31` leaf–leaf link.

## Do not

- Redistribute, add a static, or change a next hop.
- Treat a management-network ping as proof of the fabric underlay.
- Invent traceroute hops.

## How to say it

“On leaf1, 10.255.0.12/32 is B E via 10.0.1.0 (tool time); ping
from leaf1 to 10.255.0.12: N received.” If the route or ping tool
fails, stop there.
