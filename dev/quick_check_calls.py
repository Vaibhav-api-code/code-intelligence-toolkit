#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Quick check of what's calling OrderSender methods

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

from neo4j import GraphDatabase

# Connect to database
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Neo4jSecure2025'))

with driver.session() as session:
    # Check current state
    print("Current database state:")
    result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count")
    for record in result:
        print(f"  {record['label']}: {record['count']}")
    
    # Check CALLS relationships
    result = session.run("MATCH ()-[r:CALLS]->() RETURN count(r) as count")
    print(f"\nCALLS relationships: {result.single()['count']}")
    
    # Check what's calling OrderSender methods
    result = session.run("""
        MATCH (caller:Method)-[:CALLS]->(callee:Method)
        WHERE callee.class CONTAINS 'OrderSender'
        RETURN DISTINCT caller.class as caller_class, callee.signature as callee_method
        ORDER BY caller_class, callee_method
        LIMIT 20
    """)
    
    print("\nMethods calling OrderSender:")
    for record in result:
        print(f"  {record['caller_class']} -> {record['callee_method']}")
    
    # Specifically check for sendLimitBuyOrder callers
    result = session.run("""
        MATCH (caller:Method)-[:CALLS]->(callee:Method)
        WHERE callee.signature CONTAINS 'sendLimitBuyOrder'
        RETURN caller.signature, caller.class
    """)
    
    print("\nMethods calling sendLimitBuyOrder:")
    for record in result:
        print(f"  {record['caller.class']}.{record['caller.signature']}")

driver.close()
