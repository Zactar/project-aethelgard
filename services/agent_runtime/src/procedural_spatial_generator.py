#!/usr/bin/env python3
"""
PROJECT AETHELGARD: PROCEDURAL SPATIAL TOPOLOGY GENERATOR
Implements algorithmic 3D AABB layout generation, overlap validation, and smart object anchoring.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

from schemas.studio_contracts import (
    SmartObjectAnchor, SpatialRoomNode, Vector3D
)

ZONE_PREFIXES = ["Vaulted", "Sunken", "Ironbound",
                 "Shadowed", "Hearthstone", "Echoing", "Canal", "Garrison"]
ZONE_ROLES = [
    ("Storehouse", "CLANDESTINE_STORAGE", "SmartObject.Container.SmugglerCache"),
    ("Bastion", "MILITARY_CHECKPOINT", "SmartObject.Armory.WeaponRack"),
    ("Waterway", "TRANSIT_WATERWAY", "SmartObject.Mechanism.CargoCrane"),
    ("Refectory", "CIVIC_GATHERING", "SmartObject.Craft.AleCask"),
    ("Undercroft", "CLANDESTINE_ALLEY", "SmartObject.Mechanism.SluiceGate")
]


class ProceduralSpatialGenerator:
    """Algorithmic AABB room tile placement engine with collision testing."""

    def __init__(self, margin_buffer: float = 80.0):
        self.margin_buffer = margin_buffer

    def check_aabb_overlap(
        self,
        min_a: Vector3D, max_a: Vector3D,
        min_b: Vector3D, max_b: Vector3D
    ) -> bool:
        """Evaluates whether two 3D Axis-Aligned Bounding Boxes collide with boundary margins."""
        buf = self.margin_buffer
        overlap_x = (min_a.x - buf < max_b.x) and (max_a.x + buf > min_b.x)
        overlap_y = (min_a.y - buf < max_b.y) and (max_a.y + buf > min_b.y)
        overlap_z = (min_a.z < max_b.z) and (max_a.z > min_b.z)
        return overlap_x and overlap_y and overlap_z

    def generate_next_spatial_node(
        self,
        existing_nodes: Dict[str, SpatialRoomNode],
        theme_hint: str = "undercroft"
    ) -> Optional[SpatialRoomNode]:
        """Calculates a non-overlapping contiguous room node attached to an existing anchor."""
        if not existing_nodes:
            return None

        # Select candidate anchor room with fewer than 4 connections
        eligible_anchors = [
            n for n in existing_nodes.values()
            if len(n.connected_node_ids) < 4
        ]
        if not eligible_anchors:
            eligible_anchors = list(existing_nodes.values())

        anchor = random.choice(eligible_anchors)

        # Cardinal expansion steps: North, South, East, West, Downward
        directions = [
            (1.0, 0.0, 0.0),   # East
            (-1.0, 0.0, 0.0),  # West
            (0.0, 1.0, 0.0),   # South
            (0.0, -1.0, 0.0),  # North
            (0.0, 1.0, -150.0)  # Subterranean drop
        ]
        random.shuffle(directions)

        width = random.choice([1200.0, 1400.0, 1600.0])
        depth = random.choice([1000.0, 1200.0, 1400.0])
        height = random.choice([350.0, 400.0, 450.0])

        anchor_min = anchor.bounds_min
        anchor_max = anchor.bounds_max
        anchor_w = abs(anchor_max.x - anchor_min.x)
        anchor_d = abs(anchor_max.y - anchor_min.y)

        for dir_x, dir_y, dir_z in directions:
            offset_dist_x = (anchor_w / 2) + (width / 2) + 60.0
            offset_dist_y = (anchor_d / 2) + (depth / 2) + 60.0

            cand_cx = anchor.center_location.x + (dir_x * offset_dist_x)
            cand_cy = anchor.center_location.y + (dir_y * offset_dist_y)
            cand_cz = anchor.center_location.z + dir_z

            cand_min = Vector3D(x=cand_cx - (width / 2),
                                y=cand_cy - (depth / 2), z=cand_cz)
            cand_max = Vector3D(x=cand_cx + (width / 2),
                                y=cand_cy + (depth / 2), z=cand_cz + height)

            # Test collisions against all existing nodes
            collision = False
            for other_node in existing_nodes.values():
                if self.check_aabb_overlap(cand_min, cand_max, other_node.bounds_min, other_node.bounds_max):
                    collision = True
                    break

            if not collision:
                # Valid spatial slot discovered
                role_name, role_func, so_tag = random.choice(ZONE_ROLES)
                prefix = random.choice(ZONE_PREFIXES)
                node_idx = len(existing_nodes) + 1
                new_id = f"NODE_{prefix.upper()}_{role_name.upper()}_{node_idx}"
                zone_title = f"{prefix} {role_name}"

                so_anchor_id = f"SO_{prefix.upper()}_{node_idx:02d}"
                smart_obj = SmartObjectAnchor(
                    anchor_id=so_anchor_id,
                    smart_object_tag=so_tag,
                    relative_position=Vector3D(
                        x=cand_cx, y=cand_cy, z=cand_cz),
                    interaction_facing_yaw=0.0
                )

                new_node = SpatialRoomNode(
                    node_id=new_id,
                    zone_name=zone_title,
                    function=role_func,
                    bounds_min=cand_min,
                    bounds_max=cand_max,
                    center_location=Vector3D(x=cand_cx, y=cand_cy, z=cand_cz),
                    connected_node_ids=[anchor.node_id],
                    smart_objects=[smart_obj]
                )
                return new_node

        return None
