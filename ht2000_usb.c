// ht2000_usb.c
#include <libusb-1.0/libusb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define VID 0x10c4
#define PID 0x82cd
#define IFNUM 0    // HT2000 shows one interface; adjust if lsusb says otherwise
#define REPORT_ID 0x05
#define TYPE_FEATURE 3

static int set_report(libusb_device_handle *h, uint8_t report_id, const unsigned char *data, int len) {
    uint16_t wValue = (TYPE_FEATURE << 8) | report_id;
    return libusb_control_transfer(h, 0x21, 0x09, wValue, IFNUM, (unsigned char*)data, len, 1000);
}

static int get_report(libusb_device_handle *h, uint8_t report_id, unsigned char *data, int len) {
    uint16_t wValue = (TYPE_FEATURE << 8) | report_id;
    return libusb_control_transfer(h, 0xA1, 0x01, wValue, IFNUM, data, len, 1000);
}

int main(void) {
    libusb_context *ctx = NULL;
    libusb_device_handle *h = NULL;
    int r = libusb_init(&ctx);
    if (r) { fprintf(stderr, "libusb_init: %d\n", r); return 1; }

    h = libusb_open_device_with_vid_pid(ctx, VID, PID);
    if (!h) { fprintf(stderr, "device 10c4:82cd not found\n"); return 2; }

    // Detach kernel driver just in case
    libusb_detach_kernel_driver(h, IFNUM);
    r = libusb_claim_interface(h, IFNUM);
    if (r) { fprintf(stderr, "claim_interface: %d\n", r); return 3; }

    // Your code sends 0x05 [ff ff ff]
    unsigned char setbuf[3] = {0xff, 0xff, 0xff};
    r = set_report(h, REPORT_ID, setbuf, sizeof(setbuf));
    if (r < 0) fprintf(stderr, "SET_REPORT: %d\n", r);

    unsigned char buf[256] = {0};
    r = get_report(h, REPORT_ID, buf, sizeof(buf));
    if (r < 0) {
        fprintf(stderr, "GET_REPORT: %d\n", r);
        return 4;
    }

    // Parse same fields as your hidraw version
    if (r >= 30) {
        unsigned int seconds = (buf[1] << 24) | (buf[2] << 16) | (buf[3] << 8) | buf[4];
        seconds -= 2004450700U;

        time_t now = seconds;
        struct tm *p = localtime(&now);
        char ts[64]; strftime(ts, sizeof(ts), "%d-%m-%Y %H:%M:%S", p);

        double temperature = ((buf[7] << 8) | buf[8]) - 400; temperature /= 10.0;
        double humidity    = ((buf[9] << 8) | buf[10]) / 10.0;
        double co2         =  (buf[24] << 8) | buf[25];

        printf("%u, %s, %f, %f, %f\n", seconds, ts, temperature, humidity, co2);
    } else {
        fprintf(stderr, "Report 0x05 too short (%d bytes)\n", r);
        return 5;
    }

    libusb_release_interface(h, IFNUM);
    libusb_close(h);
    libusb_exit(ctx);
    return 0;
}

