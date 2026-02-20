"""End-to-end interoperability example: trajectory contract to CSV export."""

from pathlib import Path

from airspacesim.io.exporters import export_trajectory_json_to_csv
from airspacesim.settings import settings


def main():
    input_path = Path(settings.TRAJECTORY_FILE)
    output_path = input_path.with_name("trajectory_export.csv")
    export_trajectory_json_to_csv(str(input_path), str(output_path))
    print(f"Exported trajectory CSV: {output_path}")


if __name__ == "__main__":
    main()
