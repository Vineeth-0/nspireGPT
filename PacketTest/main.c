#include <os.h>
#include <libndls.h>
#include <stdint.h>
#include <string.h>

#define SERVICE_STREAM 0x04

static nn_ch_t ch;
static int connected = 0;

static void navnet_init()
{
    nn_oh_t oh = TI_NN_CreateOperationHandle();
    nn_nh_t node;

    if (TI_NN_NodeEnumInit(oh) < 0) return;
    if (TI_NN_NodeEnumNext(oh, &node) < 0) return;

    TI_NN_NodeEnumDone(oh);

    if (TI_NN_Connect(node, SERVICE_STREAM, &ch) >= 0) {
        connected = 1;
    }

    TI_NN_DestroyOperationHandle(oh);
}

static void send_msg(const char *msg)
{
    if (!connected)
        navnet_init();

    if (!connected)
        return;

    TI_NN_Write(ch, (void *)msg, strlen(msg));
}

int main(void)
{
    assert_ndless_rev(893);

    printf("NavNet stream running...\n");

    navnet_init();

    int i = 0;
    char buf[64];

    while (1)
    {
        sprintf(buf, "MSG_%d", i++);
        send_msg(buf);

        sleep(1);  // IMPORTANT: prevents CX II crashes
    }

    return 0;
}