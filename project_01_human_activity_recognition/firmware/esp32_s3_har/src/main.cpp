#include <Arduino.h>
#include <Wire.h>

#define MPU6050_ADDR 0x68

#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9

#define MPU6050_PWR_MGMT_1 0x6B
#define MPU6050_ACCEL_XOUT_H 0x3B
#define MPU6050_WHO_AM_I 0x75

struct ImuRawData {
    int16_t acc_x;
    int16_t acc_y;
    int16_t acc_z;
    int16_t temp;
    int16_t gyro_x;
    int16_t gyro_y;
    int16_t gyro_z;
};

void writeMpuRegister(uint8_t reg, uint8_t value) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(reg);
    Wire.write(value);
    Wire.endTransmission();
}

uint8_t readMpuRegister(uint8_t reg) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(reg);

    if (Wire.endTransmission(false) != 0) {
        return 0xFF;
    }

    Wire.requestFrom(MPU6050_ADDR, 1);

    if (Wire.available()) {
        return Wire.read();
    }

    return 0xFF;
}

bool readMpuRawData(ImuRawData &data) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(MPU6050_ACCEL_XOUT_H);

    if (Wire.endTransmission(false) != 0) {
        return false;
    }

    uint8_t bytesRead = Wire.requestFrom(MPU6050_ADDR, 14);

    if (bytesRead != 14) {
        return false;
    }

    data.acc_x = (Wire.read() << 8) | Wire.read();
    data.acc_y = (Wire.read() << 8) | Wire.read();
    data.acc_z = (Wire.read() << 8) | Wire.read();
    data.temp   = (Wire.read() << 8) | Wire.read();
    data.gyro_x = (Wire.read() << 8) | Wire.read();
    data.gyro_y = (Wire.read() << 8) | Wire.read();
    data.gyro_z = (Wire.read() << 8) | Wire.read();

    return true;
}

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println();
    Serial.println("ESP32-S3 MPU6050 Raw Reading Test");

    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(100000);

    uint8_t who_am_i = readMpuRegister(MPU6050_WHO_AM_I);

    Serial.print("MPU6050 WHO_AM_I: 0x");
    Serial.println(who_am_i, HEX);

    if (who_am_i != 0x68) {
        Serial.println("Warning: unexpected WHO_AM_I value. Check sensor/address.");
    }

    writeMpuRegister(MPU6050_PWR_MGMT_1, 0x00);
    delay(100);

    Serial.println("MPU6050 initialization done");
}

void loop() {
    ImuRawData imu;

    if (readMpuRawData(imu)) {
        Serial.print("acc_raw_x: ");
        Serial.print(imu.acc_x);

        Serial.print(" | acc_raw_y: ");
        Serial.print(imu.acc_y);

        Serial.print(" | acc_raw_z: ");
        Serial.print(imu.acc_z);

        Serial.print(" | gyro_raw_x: ");
        Serial.print(imu.gyro_x);

        Serial.print(" | gyro_raw_y: ");
        Serial.print(imu.gyro_y);

        Serial.print(" | gyro_raw_z: ");
        Serial.println(imu.gyro_z);
    } else {
        Serial.println("Failed to read MPU6050 raw data.");
    }

    delay(500);
}
