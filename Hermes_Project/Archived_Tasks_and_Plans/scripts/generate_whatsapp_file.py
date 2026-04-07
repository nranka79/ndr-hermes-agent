
import urllib.parse

def generate_message(contact_number=""):
    message = """Hi Sashi Dharan,

Here's a clear explanation of how the current investors are securing their 176,612 sq ft of the property.

As it stands, out of the total project plot cost, ₹21 Crores is attributed to the land value, accompanied by ₹6.0 Crores allocated for development and ₹1.2 Crores for miscellaneous costs, aggregating to a total project cost of roughly ₹28.2 Crores.

Based on our agreement, Group 1 holds a 50% financial commitment, while taking up 60% of the land area.

This arrangement means the remaining portion (₹14.1 Crores representing 50% of the cost burden) is to be borne by the Group 2 investors (P1-P19), who hold a 40% share of the overall land piece (117,612 sq ft). This translates to an effective entry cost equivalent of approx ₹1198.86 per sq ft.

We established that the early investors who brought in resources initially and locked the land area in, with an added 10% premium space allocation, maintain a solid stake based on our agreement with Group 1.

Please feel free to reach out if you have further queries about these calculations or the general break up."""

    encoded_message = urllib.parse.quote(message)
    if contact_number:
        # Assuming the number should be passed without '+' or leading zeros, e.g., '919876543210'
        whatsapp_link = f"https://wa.me/{contact_number}?text={encoded_message}"
    else:
        whatsapp_link = f"https://wa.me/?text={encoded_message}"
        
    print(f"WhatsApp Link:\n{whatsapp_link}")
    
    with open('whatsapp_sashi.txt', 'w', encoding='utf-8') as f:
        f.write(whatsapp_link)

if __name__ == '__main__':
    generate_message()
