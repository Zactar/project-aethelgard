#!/usr/bin/env python3
"""
PROJECT AETHELGARD: PROCEDURAL SPATIAL TOPOLOGY GENERATOR
Algorithmic 3D AABB room layout engine with non-colliding boundary placement.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

from schemas.studio_contracts import (
    SmartObjectAnchor, SpatialRoomNode, Vector3D
)

ZONE_ROLES = [
    ("Garrison Bastion", "MILITARY_CHECKPOINT", "SmartObject.Armory.WeaponRack"),
    ("Undercroft Ossuary", "CLANDESTINE_STORAGE",
     "SmartObject.Container.SmugglerCache"),
    ("Canal Sluice Concourse", "TRANSIT_WATERWAY",
     "SmartObject.Mechanism.CargoCrane"),
    ("High Seat Sanctum", "CIVIC_GATHERING", "SmartObject.Civic.RallyPoint"),
    ("Barricade Gatehouse", "MILITARY_CHECKPOINT",
     "SmartObject.Mechanism.SluiceGate")
]


class ProceduralSpatialGenerator:
    """Algorithmic AABB room tile placement engine with collision testing."""

    def __init__(self, margin_buffer: float = 120.0):
        self.margin_buffer = margin_buffer

    def check_aabb_overlap(
        self,
        min_a: Vector3D, max_a: Vector3D,
        min_b: Vector3D, max_b: Vector3D
    ) -> bool:
        """Evaluates whether two 3D Axis-Aligned Bounding Boxes collide."""
        overlap_x = (min_a.x < max_b.x) and (max_a.x > min_b.x)
        overlap_y = (min_a.y < max_b.y) and (max_a.y > min_b.y)
        overlap_z = (min_a.z < max_b.z) and (max_a.z > min_b.z)
        return overlap_x and overlap_y and overlap_z

    def generate_next_spatial_node(
        self,
        existing_nodes: Dict[str, SpatialRoomNode],
        theme_hint: str = "garrison"
    ) -> Optional[SpatialRoomNode]:
        """Calculates a non-overlapping room node attached to an existing anchor."""
        if not existing_nodes:
            return None

        # Test across all anchors to prevent deadlock on a single congested room
        anchors = list(existing_nodes.values())
        random.shuffle(anchors)

        directions = [
            (1.0, 0.0, 0.0),    # East
            (-1.0, 0.0, 0.0),   # West
            (0.0, 1.0, 0.0),    # South
            (0.0, -1.0, 0.0),   # North
            (0.0, 1.2, -180.0)  # Subterranean drop
        ]

        width = 1400.0
        depth = 1200.0
        height = 400.0

        for anchor in anchors:
            anchor_min = anchor.bounds_min
            anchor_max = anchor.bounds_max
            anchor_w = abs(anchor_max.x - anchor_min.x)
            anchor_d = abs(anchor_max.y - anchor_min.y)

            for dir_x, dir_y, dir_z in directions:
                # Add 250 units clearance between rooms
                offset_dist_x = (anchor_w / 2.0) + (width / 2.0) + 250.0
                offset_dist_y = (anchor_d / 2.0) + (depth / 2.0) + 250.0

                cand_cx = anchor.center_location.x + (dir_x * offset_dist_x)
                cand_cy = anchor.center_location.y + (dir_y * offset_dist_y)
                cand_cz = anchor.center_location.z + dir_z

                cand_min = Vector3D(x=cand_cx - (width / 2.0),
                                    y=cand_cy - (depth / 2.0), z=cand_cz)
                cand_max = Vector3D(x=cand_cx + (width / 2.0),
                                    y=cand_cy + (depth / 2.0), z=cand_cz + height)

                collision = False
                for other_id, other_node in existing_nodes.items():
                    if self.check_aabb_overlap(cand_min, cand_max, other_node.bounds_min, other_node.bounds_max):
                        collision = True
                        break

                if not collision:
                    role_name, role_func, so_tag = random.choice(ZONE_ROLES)
                    node_idx = len(existing_nodes) + 1
                    clean_tag = role_name.upper().replace(" ", "_")
                    new_id = f"NODE_{clean_tag}_{node_idx}"

                    smart_obj = SmartObjectAnchor(
                        anchor_id=f"SO_{clean_tag[:6]}_{node_idx:02d}",
                        smart_object_tag=so_tag,
                        relative_position=Vector3D(
                            x=cand_cx, y=cand_cy, z=cand_cz),
                        interaction_facing_yaw=0.0
                    )

                    return SpatialRoomNode(
                        node_id=new_id,
                        zone_name=f"{role_name} {node_idx}",
                        function=role_func,
                        bounds_min=cand_min,
                        bounds_max=cand_max,
                        center_location=Vector3D(
                            x=cand_cx, y=cand_cy, z=cand_cz),
                        connected_node_ids=[anchor.node_id],
                        smart_objects=[smart_obj]
                    )

        return None
