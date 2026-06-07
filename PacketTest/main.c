#include <os.h>
#include <libndls.h>
#include <string.h>

#define SERVICE 0x1234

static nn_ch_t ch;
static int ok = 0;

void init()
{
    nn_oh_t oh = TI_NN_CreateOperationHandle();
    nn_nh_t node;

    if (TI_NN_NodeEnumInit(oh) < 0) return;
    if (TI_NN_NodeEnumNext(oh, &node) < 0) return;
    TI_NN_NodeEnumDone(oh);

    ok = (TI_NN_Connect(node, SERVICE, &ch) >= 0);

    TI_NN_DestroyOperationHandle(oh);
}

void send(const char *msg)
{
    if (!ok) return;
    TI_NN_Write(ch, (void*)msg, strlen(msg));
}

int main()
{
    assert_ndless_rev(893);

    init();

    int i = 0;
    char buf[64];

    while (1)
    {
        sprintf(buf, "hello %d", i++);
        send(buf);

        msleep(1000);
    }

    return 0;
}