from collections import defaultdict
import numpy as np


MOVEMENT_EVENTS = {"Position", "BotPosition"}
COMBAT_EVENTS = {"Kill", "BotKill"}
DEATH_EVENTS = {"Killed", "BotKilled"}
STORM_EVENTS = {"KilledByStorm"}
LOOT_EVENTS = {"Loot"}


class AnalyticsService:
    def __init__(self, match_service, grid_size=64):
        self.match_service = match_service
        self.grid_size = grid_size

    def _build_grid(self, df):
        grid = {
            "movement": np.zeros((self.grid_size, self.grid_size), dtype=np.int32),
            "combat": np.zeros((self.grid_size, self.grid_size), dtype=np.int32),
            "loot": np.zeros((self.grid_size, self.grid_size), dtype=np.int32),
            "death": np.zeros((self.grid_size, self.grid_size), dtype=np.int32),
            "storm": np.zeros((self.grid_size, self.grid_size), dtype=np.int32),
        }

        sector_stats = defaultdict(lambda: {
            "movement": 0,
            "combat": 0,
            "loot": 0,
            "death": 0,
            "storm": 0
        })

        for row in df.itertuples():

            if np.isnan(row.pixel_x) or np.isnan(row.pixel_y):
                continue

            gx = min(
                self.grid_size - 1,
                max(0, int((row.pixel_x / 1024) * self.grid_size))
            )

            gy = min(
                self.grid_size - 1,
                max(0, int((row.pixel_y / 1024) * self.grid_size))
            )

            sector = f"{chr(65 + gx // 8)}{gy // 8 + 1}"

            if row.event in MOVEMENT_EVENTS:
                grid["movement"][gy, gx] += 1
                sector_stats[sector]["movement"] += 1

            elif row.event in COMBAT_EVENTS:
                grid["combat"][gy, gx] += 1
                sector_stats[sector]["combat"] += 1

            elif row.event in LOOT_EVENTS:
                grid["loot"][gy, gx] += 1
                sector_stats[sector]["loot"] += 1

            elif row.event in DEATH_EVENTS:
                grid["death"][gy, gx] += 1
                sector_stats[sector]["death"] += 1

            elif row.event in STORM_EVENTS:
                grid["storm"][gy, gx] += 1
                sector_stats[sector]["storm"] += 1

        unused = []

        for gy in range(self.grid_size):
            for gx in range(self.grid_size):

                if (
                    grid["movement"][gy, gx] == 0
                    and grid["combat"][gy, gx] == 0
                    and grid["loot"][gy, gx] == 0
                ):
                    unused.append([gx, gy])

        def top_sector(key):

            if not sector_stats:
                return None

            return max(
                sector_stats.items(),
                key=lambda x: x[1][key]
            )[0]

        summary = {
            "matches": int(df.match_id.nunique()),
            "players": int(df.user_id.nunique()),
            "movement_events": int((df.event.isin(MOVEMENT_EVENTS)).sum()),
            "combat_events": int((df.event.isin(COMBAT_EVENTS)).sum()),
            "loot_events": int((df.event == "Loot").sum()),
            "deaths": int((df.event.isin(DEATH_EVENTS)).sum()),
            "storm_deaths": int((df.event == "KilledByStorm").sum()),
            "unused_cells": len(unused),
            "total_cells": self.grid_size * self.grid_size,
            "unused_percent": round(
                len(unused) * 100 / (self.grid_size * self.grid_size),
                2
            ),
            "highest_combat_sector": top_sector("combat"),
            "highest_death_sector": top_sector("death"),
            "highest_loot_sector": top_sector("loot"),
            "highest_movement_sector": top_sector("movement"),
        }

        return {
            "grid_size": self.grid_size,
            "movement": grid["movement"].tolist(),
            "combat": grid["combat"].tolist(),
            "loot": grid["loot"].tolist(),
            "death": grid["death"].tolist(),
            "storm": grid["storm"].tolist(),
            "unused": unused,
            "summary": summary,
        }

    def day_summary(self, date):

        self.match_service.load()

        df = self.match_service.df

        day_df = df[df["date"] == date]

        if day_df.empty:
            return None

        return self._build_grid(day_df)

    def map_summary(self, map_id):

        self.match_service.load()

        df = self.match_service.df

        map_df = df[df["map_id"] == map_id]

        if map_df.empty:
            return None

        return self._build_grid(map_df)

    def overall_summary(self):

        self.match_service.load()

        return self._build_grid(self.match_service.df)