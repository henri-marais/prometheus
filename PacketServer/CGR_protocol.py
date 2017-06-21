from datetime import datetime

def CGR_TimeStamp(raw_packet):
    PacketTime = datetime(( (raw_packet[2]) >> 4) * 10 + ((raw_packet[2]) & 0x0F) + 2000,
                                   (((raw_packet[3]) >> 4) * 10 + ((raw_packet[3]) & 0x0F)),
                                   (((raw_packet[4]) >> 4) * 10 + ((raw_packet[4]) & 0x0F)),
                                   (((raw_packet[5]) >> 4) * 10 + ((raw_packet[5]) & 0x0F)),
                                   (((raw_packet[6]) >> 4) * 10 + ((raw_packet[6]) & 0x0F)),
                                   (((raw_packet[7]) >> 4) * 10 + ((raw_packet[7]) & 0x0F)),
                                   ((raw_packet[8])) * 5 * 1000)
    return PacketTime

def CGR_Type(raw_packet):
    if ((raw_packet[1]) & 0x0F) == 1:
        return 'Heartbeat'
    if ((raw_packet[1]) & 0x0F) == 2:
        return 'Starting'
    if ((raw_packet[1]) & 0x0F) == 3:
        return 'Started'
    if ((raw_packet[1]) & 0x0F) == 4:
        return 'Running'
    if ((raw_packet[1]) & 0x0F) == 5:
        return 'Shutdown'
    else:
        return 'Unknown'

def CGR_Data(raw_packet):
    int_fract = (((raw_packet[9]) >> 4) * 10) + ((raw_packet[9]) & 0x0F)
    dec_fract = (((raw_packet[10]) >> 4) * 10) + ((raw_packet[10]) & 0x0F)
    return int_fract + dec_fract / 100
# def CGR_TimeStamp(raw_packet):
#     PacketTime = datetime((ord(raw_packet[2]) >> 4) * 10 + (ord(raw_packet[2]) & 0x0F) + 2000,
#                                    ((ord(raw_packet[3]) >> 4) * 10 + (ord(raw_packet[3]) & 0x0F)),
#                                    ((ord(raw_packet[4]) >> 4) * 10 + (ord(raw_packet[4]) & 0x0F)),
#                                    ((ord(raw_packet[5]) >> 4) * 10 + (ord(raw_packet[5]) & 0x0F)),
#                                    ((ord(raw_packet[6]) >> 4) * 10 + (ord(raw_packet[6]) & 0x0F)),
#                                    ((ord(raw_packet[7]) >> 4) * 10 + (ord(raw_packet[7]) & 0x0F)),
#                                    (ord(raw_packet[8])) * 5 * 1000)
#     return PacketTime

# def CGR_Type(raw_packet):
#     if (ord(raw_packet[1]) & 0x0F) == 1:
#         return 'Heartbeat'
#     if (ord(raw_packet[1]) & 0x0F) == 2:
#         return 'Starting'
#     if (ord(raw_packet[1]) & 0x0F) == 3:
#         return 'Started'
#     if (ord(raw_packet[1]) & 0x0F) == 4:
#         return 'Running'
#     if (ord(raw_packet[1]) & 0x0F) == 5:
#         return 'Shutdown'
#     else:
#         return 'Unknown'
#
# def CGR_Data(raw_packet):
#     int_fract = ((ord(raw_packet[9]) >> 4)*10)+(ord(raw_packet[9]) & 0x0F);
#     dec_fract = ((ord(raw_packet[10]) >> 4)*10)+(ord(raw_packet[10]) & 0x0F);
#     return int_fract+dec_fract/10