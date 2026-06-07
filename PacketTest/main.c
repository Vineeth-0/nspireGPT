#include <os.h>
#include <libndls.h>
#include <stdint.h>
#include <string.h>

#define SERVICE_STREAM 0x04

static nn_ch_t ch;
static int connected = 0;

static void init_stream()
{
    nn_oh_t oh;
    nn_nh_t node;
    int16_t rc;

    oh = TI_NN_CreateOperationHandle();

    rc = TI_NN_NodeEnumInit(oh);
    if (rc < 0) return;

    rc = TI_NN_NodeEnumNext(oh, &node);
    if (rc < 0) {
        TI_NN_NodeEnumDone(oh);
        TI_NN_DestroyOperationHandle(oh);
        return;
    }

    TI_NN_NodeEnumDone(oh);

    rc = TI_NN_Connect(node, SERVICE_STREAM, &ch);
    if (rc < 0) {
        TI_NN_DestroyOperationHandle(oh);
        return;
    }

    connected = 1;
    TI_NN_DestroyOperationHandle(oh);
}

static void send_message(const char *msg)
{
    if (!connected)
        init_stream();

    if (!connected)
        return;

    char buffer[128];

    // SIMPLE STREAM FORMAT (IMPORTANT)
    snprintf(buffer, sizeof(buffer), "%s\n", msg);

    TI_NN_Write(ch, buffer, strlen(buffer));
}

int main(void)
{
    printf("Starting stream sender...\n");

    init_stream();

    int i = 0;
    while (1)
    {
        char msg[64];
        snprintf(msg, sizeof(msg), "HELLO %d", i++);
        send_message(msg);

        msleep(500);
    }

    return 0;
}