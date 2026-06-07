/**
 * calc_sender.c
 * TI-Nspire -> Computer packet sender using the NavNet API (Ndless SDK)
 *
 * Requires Ndless v3.1 r893 or later.
 * All TI_NN_* types and prototypes come from os.h -> syscall-decls.h / nucleus.h.
 */

#include <os.h>
#include <libndls.h>
#include <string.h>

/* Custom service ID — mirror this in your computer-side listener.
 * Must not clash with TI standard IDs (e.g. 0x4060 for file transfer). */
#define MY_SERVICE_ID  0x8001u

/* Packet layout — adjust to whatever your app needs. */
typedef struct {
    uint8_t cmd;
    char    text[64];
} MyPacket;

static int nn_fail(const char *func, int16_t ret)
{
    printf("NavNet error in %s: %d\n", func, (int)ret);
    wait_key_pressed();
    return -1;
}

static int send_packet(const void *data, uint32_t data_len)
{
    nn_oh_t oh;
    nn_nh_t nh;
    nn_ch_t ch;
    int16_t rc;

    oh = TI_NN_CreateOperationHandle();
    if (!oh) return nn_fail("CreateOperationHandle", -1);

    rc = TI_NN_NodeEnumInit(oh);
    if (rc < 0) { TI_NN_DestroyOperationHandle(oh); return nn_fail("NodeEnumInit", rc); }

    rc = TI_NN_NodeEnumNext(oh, &nh);
    if (rc < 0) { TI_NN_NodeEnumDone(oh); TI_NN_DestroyOperationHandle(oh); return nn_fail("NodeEnumNext", rc); }

    rc = TI_NN_NodeEnumDone(oh);
    if (rc < 0) { TI_NN_DestroyOperationHandle(oh); return nn_fail("NodeEnumDone", rc); }

    rc = TI_NN_Connect(nh, MY_SERVICE_ID, &ch);
    if (rc < 0) { TI_NN_DestroyOperationHandle(oh); return nn_fail("Connect", rc); }

    rc = TI_NN_Write(ch, (void *)data, data_len);
    if (rc < 0) {
        TI_NN_Disconnect(ch);
        TI_NN_DestroyOperationHandle(oh);
        return nn_fail("Write", rc);
    }

    printf("Sent %u byte(s) OK.\n", (unsigned)data_len);

    TI_NN_Disconnect(ch);
    TI_NN_DestroyOperationHandle(oh);
    return 0;
}

int main(void)
{
    assert_ndless_rev(893);

    MyPacket pkt;
    pkt.cmd = 0x01;
    strncpy(pkt.text, "Hello from TI-Nspire!", sizeof(pkt.text) - 1);
    pkt.text[sizeof(pkt.text) - 1] = '\0';

    printf("Connecting to computer (service 0x%04X)...\n", MY_SERVICE_ID);

    if (send_packet(&pkt, sizeof(pkt)) == 0)
        printf("Done!\n");
    else
        printf("Transfer failed.\n");

    wait_key_pressed();
    return 0;
}

/* =======================================================================
 * COMPUTER-SIDE LISTENER  (compile separately on Windows/Linux)
 *
 * Build:  gcc listener.c -o listener -L./ndless_pc -lnavnet
 *         (ensure navnet.dll is on PATH at runtime on Windows)
 *
 * #include "navnet.h"
 * #include <stdio.h>
 * #include <stdint.h>
 *
 * #define MY_SERVICE_ID 0x8001u
 * typedef struct { uint8_t cmd; char text[64]; } MyPacket;
 *
 * void service_cb(nn_ch_t ch, void *data) {
 *     MyPacket pkt;
 *     uint32_t recv_size = 0;
 *     TI_NN_Read(ch, 10000, &pkt, sizeof(pkt), &recv_size);
 *     if (recv_size > 0)
 *         printf("cmd=0x%02X  text=%s\n", pkt.cmd, pkt.text);
 * }
 *
 * int main(void) {
 *     TI_NN_Init("-c 1 -d 0");  // Student Software must NOT be running
 *     TI_NN_StartService(MY_SERVICE_ID, NULL, service_cb);
 *     printf("Listening... press Enter to quit.\n");
 *     getchar();
 *     TI_NN_StopService(MY_SERVICE_ID);
 *     TI_NN_Shutdown();
 *     return 0;
 * }
 * ======================================================================= */