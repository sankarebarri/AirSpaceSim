import json

class MapRenderer:
    def __init__(self, center=None, zoom=10):
        """
        Initialize the map with a center and zoom level.

        :param center: List of [latitude, longitude] for the map center. Default: [0, 0].
        :param zoom: Integer zoom level. Default: 10.
        """
        self.center = center or [0, 0]
        self.zoom = zoom
        self.tile_layer = None
        self.elements = []

    def add_tile_layer(self, url=None, attribution=None):
        """
        Add a tile layer to the map. Default is OpenStreetMap.

        :param url: Tile layer URL template. Default: OpenStreetMap.
        :param attribution: Attribution for the map tiles.
        """
        self.tile_layer = {
            "url": url or "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": attribution or "© OpenStreetMap contributors"
        }

    def add_polygon_boundary(self, coords, color="blue", name=None):
        """
        Add a polygon to represent an airspace boundary.

        :param coords: List of [latitude, longitude] pairs for the polygon.
        :param color: Color of the polygon. Default: blue.
        :param name: Optional name for the polygon.
        """
        self.elements.append({
                "type": "polygon",
                "coords": coords,
                "color": color,
                "name": name
        })

    def add_circle_boundary(self, center, radius, name=None, color="blue", fill_color="blue", fill_opacity=0.2, dash_array=None, opacity=1):
        """
        Add a circle to represent an airspace boundary.

        :param center: [latitude, longitude] for the circle's center.
        :param radius: Radius of the circle in meters.
        :param name: Optional name for the circle.
        :param color: Border color of the circle. Default: blue.
        :param fill_color: Fill color of the circle. Default: blue.
        :param fill_opacity: Opacity of the fill. Default: 0.2.
        :param dash_array: Optional dash pattern for the border.
        :param opacity: Opacity of the border. Default: 1.
        """
        self.elements.append({
            "type": "circle",
            "center": center,
            "radius": radius,
            "name": name,
            "color": color,
            "fill_color": fill_color,
            "fill_opacity": fill_opacity,
            "dash_array": dash_array,  # Add dash_array
            "opacity": opacity         # Add opacity
        })

    def add_polyline(self, coords, color="green", weight=3, opacity=1, name=None):
        """
        Add a polyline to represent a route.

        :param coords: List of [latitude, longitude] pairs for the polyline.
        :param color: Color of the polyline. Default: green.
        :param weight: Thickness of the polyline. Default: 3.
        :param opacity: Opacity of the polyline. Default: 1.
        :param name: Optional name for the polyline.
        """
        self.elements.append({
            "type": "polyline",
            "coords": coords,
            "color": color,
            "weight": weight,
            "opacity": opacity,
            "name": name
        })


    def add_marker(self, coords, popup_text=None, icon_url=None, icon_size=None, label_text=None):
        """
        Add a marker to represent a waypoint with optional permanent labels.

        :param coords: [latitude, longitude] of the marker.
        :param popup_text: Optional text to display on marker click.
        :param icon_url: URL for a custom icon (e.g., triangle).
        :param icon_size: Size of the custom icon as [width, height]. Default: [20, 20].
        :param label_text: Optional text to display as a permanent label near the marker.
        """
        self.elements.append({
            "type": "marker",
            "coords": coords,
            "popup_text": popup_text,
            "icon_url": icon_url,
            "icon_size": icon_size or [20, 20],  # Default size if not provided
            "label_text": label_text  # Permanent label
        })


    def show(self, output_file="map.html"):
        """
        Render the map and save it to an HTML file.

        :param output_file: Name of the HTML file to save the map. Default: map.html.
        """
        map_data = {
            "center": self.center,
            "zoom": self.zoom,
            "tile_layer": self.tile_layer,
            "elements": self.elements
        }
        # Generate the HTML/JavaScript using Leaflet.js
        html_content = self._generate_html(map_data)
        with open(output_file, "w") as f:
            f.write(html_content)
        print(f"Map has been rendered and saved to {output_file}.")

    def _generate_html(self, map_data):
        """
        Internal method to generate HTML content for the map.

        :param map_data: Dictionary containing map configuration and elements.
        :return: String containing the HTML content.
        """
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                <style>
                    #map {{ width: 100%; height: 700px; }}
                </style>
            </head>
            <body>
                <div id="map"></div>
                <script>
                    const map = L.map("map").setView({map_data["center"]}, {map_data["zoom"]});
                    L.tileLayer("{map_data['tile_layer']['url']}", {{
                        attribution: "{map_data['tile_layer']['attribution']}",
                        maxZoom: 19
                    }}).addTo(map);

                    {self._generate_elements_js(map_data["elements"])}
                </script>
            </body>
        </html>
        """

    def _generate_elements_js(self, elements):
        """
        Internal method to generate JavaScript for map elements.

        :param elements: List of elements (circle, polygons, polylines, markers).
        :return: JavaScript code to add elements to the map.
        """
        js_code = ""
        for element in elements:
            if element["type"] == "circle":
                js_code += f"""
                L.circle({json.dumps(element["center"])}, {{
                    radius: {element["radius"]},
                    color: "{element['color']}",
                    fillColor: "{element['fill_color']}",
                    fillOpacity: {element['fill_opacity']},
                    opacity: {element['opacity']},
                    dashArray: "{element['dash_array'] or ''}"  // Apply dash pattern if provided
                }}).addTo(map).bindPopup("{element['name'] or ''}");
                """
            elif element["type"] == "polygon":
                js_code += f"""
                L.polygon({json.dumps(element["coords"])}, {{
                    color: "{element['color']}"
                }}).addTo(map).bindPopup("{element['name'] or ''}")
                """
            elif element["type"] == "polyline":
                js_code += f"""
                L.polyline({json.dumps(element['coords'])}, {{
                    color: "{element['color']}",
                    weight: {element['weight']},  // Line thickness
                    opacity: {element['opacity']}  // Line opacity
                }}).addTo(map).bindPopup("{element['name'] or ''}");
                """
            elif element["type"] == "marker":
                if element["icon_url"]:
                    js_code += f"""
                    L.marker({json.dumps(element['coords'])}, {{
                        icon: L.icon({{
                            iconUrl: "{element['icon_url']}",
                            iconSize: {json.dumps(element['icon_size'])}
                        }})
                    }}).addTo(map).bindPopup("{element['popup_text'] or ''}")
                    .bindTooltip("{element['label_text'] or ''}", {{ permanent: true, direction: "top" }});
                    """
                else:
                    js_code += f"""
                    L.marker({json.dumps(element['coords'])}).addTo(map).bindPopup("{element['popup_text'] or ''}");
                    """
        return 1