# PINS.sh -- kit S593_ORDER_ENGINE_ONE_SOURCE: the TO pins of the six files the installer places (md5 of the built files; the installer
# compares make_s593.py's output and the placed files with these) and of the clone's DUTY_MAP.json after the publish. FROM pins live in
# the installer and in make_s593.py (the brief, section 1).
declare -A TO
TO[order_rules.py]=8d078dbe1b63a4706dc6f35e3c31ac9a
TO[porders.py]=78ea72be7d87a7c56c65de7d4c96a952
TO[porders_s454.py]=40f1755a7655deb733765456b9a466fe
TO[order_sheet.py]=1f1e85c12c64521b50a10cea48220170
TO[darpan_kal.py]=325d988c61e1c7408a2a4b687a4822bb
TO[spine/spine_read.py]=827b00402add288d028c910128084b90
DMAP_TO=c2ef9c6c5adb8c930b21bff5441cc017
