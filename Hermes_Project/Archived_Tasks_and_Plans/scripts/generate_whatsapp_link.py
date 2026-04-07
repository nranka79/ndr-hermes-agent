
message = """Hi Sashi Dharan,

Here's an explanation of how the current investors are securing their 176,612 sq ft of the property.

As it stands, out of the total project plot cost, ₹21 Crores is attributed to the land value, accompanied by ₹6 Crores allocated for development and ₹1.2 Crores for miscellaneous costs, aggregating to a total project cost of roughly ₹28.2 Crores. 

Based on the total land value, Group 1 holds a 50% financial commitment, while taking up 60% of the land.

This arrangement means the remaining portion (₹14.1 Crores representing 50% of the cost burden) is to be borne by the Group 2 investors (P1-P19), who hold a 40% share of the overall land piece. This translates to an effective entry cost equivalent of approx ₹1198.86 per sq ft. 

We established that the other investors who brought in resources initially and locked the land area in, with an added 10% premium space allocation, maintain a solid stake based on our agreement with Group 1.

Please feel free to reach out if you have further queries about these calculations or the general break up."""

import urllib.parse
encoded_message = urllib.parse.quote(message)
whatsapp_link = f"https://wa.me/?text={encoded_message}"
print(f"WhatsApp Link:\n{whatsapp_link}")
