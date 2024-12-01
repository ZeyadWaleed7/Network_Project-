from PIL import Image
import socket as s
import time
import matplotlib.pyplot as plt

def image_to_bits(image_path):
    img = Image.open(image_path)
    binary_data = img.tobytes()
    bits = ""
    for byte in binary_data:
        binary_string = format(byte, '08b')
        bits += binary_string

    return bits, img.size

def bits_to_image(bits, image_size):
    bytes_array = [bits[i:i+8] for i in range(0, len(bits), 8)]
    bytes_data = bytes([int(byte, 2) for byte in bytes_array])
    img = Image.frombytes("RGB", image_size, bytes_data)

    return img

# Example:
input_image_path = "small_file.jpeg"
#output_image_path = "abdo.jpeg"

bits, image_size = image_to_bits(input_image_path)

reconstructed_img = bits_to_image(bits, image_size)

# Save the reconstructed image
#reconstructed_img.save(output_image_path)

print("Image reconstructed successfully!")


def divide_packets(bits, packet_size):
    packets = []
    num_packets = len(bits) // packet_size

    for i in range(num_packets):
        packet = bits[i*packet_size : (i+1)*packet_size]
        packets.append(packet)

    if len(bits) % packet_size != 0:
        last_packet = bits[num_packets*packet_size:]
        packets.append(last_packet)

    return packets,num_packets


packet_size = 512
packets,packets_number = divide_packets(bits, packet_size)



packetID = 0
received_packets = 0
lost_packets = 0
start = 0
trailer = 0


def send_packets(packets, ip, port, fileID):
    client = s.socket(s.AF_INET, s.SOCK_DGRAM)
    client.settimeout(2)
    global packetID, received_packets, lost_packets, start, trailer

    packet_timings = []
    retransmissions = []

    transfer_start = time.time()
    total_bytes_sent = 0
    total_packets_sent = 0

    try:
        start = 0
        window_size = 5;
        while start < len(packets):
            for i in range(start, min(start + window_size, len(packets))):
                Packet_ID = i
                header = format(Packet_ID, '016b') + format(fileID, '016b')
                trailer = format(0x0000, '032b')
                if (packetID == len(packets)-1) :
                    trailer = format(0xFFFF, '032b')

                packet = header.encode() + packets[Packet_ID].encode() + trailer.encode()
                send_time = time.time()
                client.sendto(packet, (ip, port))
                print(f"Sent packet {i}")

                try:
                    ack_data, address = client.recvfrom(1024)
                    ack_num = int(ack_data[:16].decode(), 2)
                    print(f"Received acknowledgment for packet {ack_num}")
                    if ack_num < start:
                        retransmissions.append((i, send_time))
                        received_packets += 1
                except s.timeout:
                    print(f"Timeout: No acknowledgment received, resending from packet {start}")
                    retransmissions.append((i, send_time))
                    lost_packets += 1
                    continue

                packet_timings.append((i, send_time))
                start = i + 1
    finally:
        transfer_end = time.time()
        elapsed_time = transfer_end - transfer_start
        average_transfer_rate = total_bytes_sent / elapsed_time

        # Display sending details
        print("Transfer details:")
        print(f"Start Time: {transfer_start}")
        print(f"End Time: {transfer_end}")
        print(f"Elapsed Time: {elapsed_time:.2f} seconds")
        print(f"Total Packets Sent: {total_packets_sent}")
        print(f"Total Bytes Sent: {total_bytes_sent}")
        print(f"Received Packets: {received_packets}")
        print(f"Lost Packets: {lost_packets}")
        print(f"Average Transfer Rate: {average_transfer_rate:.2f} bytes/sec")
        client.close()

    return packet_timings, retransmissions


import matplotlib.pyplot as plt

def plot_packet_timings(packet_timings, retransmissions):
    packet_ids, times = zip(*packet_timings)
    retrans_ids, retrans_times = zip(*retransmissions) if retransmissions else ([], [])

    plt.figure(figsize=(10, 6))
    plt.scatter(times, packet_ids, color='blue', label='Normal Transmission')
    plt.scatter(retrans_times, retrans_ids, color='red', label='Retransmission')
    plt.title('Packet Transmission Times')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Packet ID')
    plt.legend()
    plt.grid(True)
    plt.show()

packet_timings, retransmissions = send_packets(packets, "127.0.0.1", 2048, 0x01)
plot_packet_timings(packet_timings, retransmissions)
