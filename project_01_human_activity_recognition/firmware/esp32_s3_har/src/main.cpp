#include <Arduino.h>
#include <Wire.h>

#define MPU6050_ADDR 0x68

#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9

#define MPU6050_PWR_MGMT_1 0x6B
#define MPU6050_ACCEL_XOUT_H 0x3B
#define MPU6050_WHO_AM_I 0x75
#define MPU6050_GYRO_CONFIG 0x1B
#define MPU6050_ACCEL_CONFIG 0x1C

#define ACCEL_SCALE_FACTOR 16384.0f
#define GYRO_SCALE_FACTOR 131.0f

struct ImuRawData {
    int16_t acc_x;
    int16_t acc_y;
    int16_t acc_z;
    int16_t temp;
    int16_t gyro_x;
    int16_t gyro_y;
    int16_t gyro_z;
};

struct ImuConvertedData {
    float acc_x_g;
    float acc_y_g;
    float acc_z_g;
    float gyro_x_dps;
    float gyro_y_dps;
    float gyro_z_dps;
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

ImuConvertedData convertImuData(const ImuRawData &raw) {
    ImuConvertedData converted;

    converted.acc_x_g = raw.acc_x / ACCEL_SCALE_FACTOR;
    converted.acc_y_g = raw.acc_y / ACCEL_SCALE_FACTOR;
    converted.acc_z_g = raw.acc_z / ACCEL_SCALE_FACTOR;

    converted.gyro_x_dps = raw.gyro_x / GYRO_SCALE_FACTOR;
    converted.gyro_y_dps = raw.gyro_y / GYRO_SCALE_FACTOR;
    converted.gyro_z_dps = raw.gyro_z / GYRO_SCALE_FACTOR;

    return converted;
}

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println();
    Serial.println("ESP32-S3 MPU6050 Unit Conversion Test");

    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(100000);

    uint8_t who_am_i = readMpuRegister(MPU6050_WHO_AM_I);

    Serial.print("MPU6050 WHO_AM_I: 0x");
    Serial.println(who_am_i, HEX);

    writeMpuRegister(MPU6050_PWR_MGMT_1, 0x00);
    delay(100);

    writeMpuRegister(MPU6050_ACCEL_CONFIG, 0x00);
    writeMpuRegister(MPU6050_GYRO_CONFIG, 0x00);

    Serial.println("Accel range: +/-2g");
    Serial.println("Gyro range: +/-250 deg/s");
    Serial.println("MPU6050 initialization done");
}

void loop() {
    ImuRawData raw;

    if (readMpuRawData(raw)) {
        ImuConvertedData imu = convertImuData(raw);

        Serial.print("RAW | ");
        Serial.print("acc_x: "); Serial.print(raw.acc_x);
        Serial.print(" | acc_y: "); Serial.print(raw.acc_y);
        Serial.print(" | acc_z: "); Serial.print(raw.acc_z);
        Serial.print(" | gyro_x: "); Serial.print(raw.gyro_x);
        Serial.print(" | gyro_y: "); Serial.print(raw.gyro_y);
        Serial.print(" | gyro_z: "); Serial.println(raw.gyro_z);

        Serial.print("UNIT | ");
        Serial.print("acc_x_g: "); Serial.print(imu.acc_x_g, 3);
        Serial.print(" | acc_y_g: "); Serial.print(imu.acc_y_g, 3);
        Serial.print(" | acc_z_g: "); Serial.print(imu.acc_z_g, 3);
        Serial.print(" | gyro_x_dps: "); Serial.print(imu.gyro_x_dps, 3);
        Serial.print(" | gyro_y_dps: "); Serial.print(imu.gyro_y_dps, 3);
        Serial.print(" | gyro_z_dps: "); Serial.println(imu.gyro_z_dps, 3);

        Serial.println();
    } else {
        Serial.println("Failed to read MPU6050 data.");
    }

    delay(500);
}
