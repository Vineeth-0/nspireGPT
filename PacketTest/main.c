#include <os.h>
#include <libndls.h>
#include <stdint.h>
#include <string.h>

#define SERVICE_STREAM 0x04

static void send_message(const char *msg)
{
    nn_oh_t oh;
    nn_nh_t node;
    nn_ch_t ch;
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

    TI_NN_Write(ch, (void *)msg, strlen(msg));

    TI_NN_Disconnect(ch);
    TI_NN_DestroyOperationHandle(oh);
}

int main(void)
{
    assert_ndless_rev(893);

    printf("Sending...\n");

    send_message("HELLO_FROM_NSPIRE");

    printf("Done\n");
    wait_key_pressed();
    return 0;
}