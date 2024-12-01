import socket as s
import time
import random
from PIL import Image

photo_data = ""

def bits_to_image(bits, image_size):
    bytes_array = [bits[i:i+8] for i in range(0, len(bits), 8)]
    bytes_data = bytes([int(byte, 2) for byte in bytes_array])
    img = Image.frombytes("RGB", image_size, bytes_data)
    return img

def receive_packets(ip, port):
    server = s.socket(s.AF_INET, s.SOCK_DGRAM)
    photo_data = ""
    sequence_number = 0
    last_packet_marker = "1111111111111111"

    try:
        server.bind((ip, port))
        while True:
            data, address = server.recvfrom(2048)
            header = data[:32].decode()
            packet_data = data[32:-32].decode()
            trailer = data[-32:].decode()

            packet_number = int(header[:16], 2)

            if packet_number == sequence_number:
                photo_data += packet_data
                print(f"Received packet {packet_number}")
                ack = format(packet_number, '016b').encode()
                server.sendto(ack, address)
                print(f"Sent ACK for packet {packet_number}")

                if trailer == last_packet_marker:
                    print("Last packet received")
                    break

                sequence_number += 1
            else:
                print(f"Packet {packet_number} out of order, discarded")
                ack = format(sequence_number - 1, '016b').encode()
                server.sendto(ack, address)
    finally:
        server.close()

    return photo_data

img = receive_packets("127.0.0.1", 2048)
img.save("out.jpeg")