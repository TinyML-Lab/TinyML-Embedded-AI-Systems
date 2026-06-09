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

#define CALIBRATION_SAMPLES 500

struct ImuRawData {
    int16_t acc_x;
    int16_t acc_y;
    int16_t acc_z;
    int16_t temp;
    int16_t gyro_x;
    int16_t gyro_y;
    int16_t gyro_z;
};

struct ImuData {
    float acc_x_g;
    float acc_y_g;
    float acc_z_g;
    float gyro_x_dps;
    float gyro_y_dps;
    float gyro_z_dps;
};

struct ImuOffsets {
    float acc_x_offset;
    float acc_y_offset;
    float acc_z_offset;
    float gyro_x_offset;
    float gyro_y_offset;
    float gyro_z_offset;
};

ImuOffsets offsets = {0, 0, 0, 0, 0, 0};

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

    Wire.requestFrom(MPU6050_ADDR, (uint8_t)1);

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

    uint8_t bytesRead = Wire.requestFrom(MPU6050_ADDR, (uint8_t)14);

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

ImuData convertRawData(const ImuRawData &raw) {
    ImuData data;

    data.acc_x_g = raw.acc_x / ACCEL_SCALE_FACTOR;
    data.acc_y_g = raw.acc_y / ACCEL_SCALE_FACTOR;
    data.acc_z_g = raw.acc_z / ACCEL_SCALE_FACTOR;

    data.gyro_x_dps = raw.gyro_x / GYRO_SCALE_FACTOR;
    data.gyro_y_dps = raw.gyro_y / GYRO_SCALE_FACTOR;
    data.gyro_z_dps = raw.gyro_z / GYRO_SCALE_FACTOR;

    return data;
}

ImuData applyCalibration(const ImuData &data) {
    ImuData calibrated;

    calibrated.acc_x_g = data.acc_x_g - offsets.acc_x_offset;
    calibrated.acc_y_g = data.acc_y_g - offsets.acc_y_offset;
    calibrated.acc_z_g = data.acc_z_g - offsets.acc_z_offset;

    calibrated.gyro_x_dps = data.gyro_x_dps - offsets.gyro_x_offset;
    calibrated.gyro_y_dps = data.gyro_y_dps - offsets.gyro_y_offset;
    calibrated.gyro_z_dps = data.gyro_z_dps - offsets.gyro_z_offset;

    return calibrated;
}

void calibrateMpu6050() {
    Serial.println("Calibration started.");
    Serial.println("Keep the sensor completely still...");

    float acc_x_sum = 0;
    float acc_y_sum = 0;
    float acc_z_sum = 0;
    float gyro_x_sum = 0;
    float gyro_y_sum = 0;
    float gyro_z_sum = 0;

    int valid_samples = 0;

    for (int i = 0; i < CALIBRATION_SAMPLES; i++) {
        ImuRawData raw;

        if (readMpuRawData(raw)) {
            ImuData data = convertRawData(raw);

            acc_x_sum += data.acc_x_g;
            acc_y_sum += data.acc_y_g;
            acc_z_sum += data.acc_z_g;

            gyro_x_sum += data.gyro_x_dps;
            gyro_y_sum += data.gyro_y_dps;
            gyro_z_sum += data.gyro_z_dps;

            valid_samples++;
        }

        delay(5);
    }

    if (valid_samples == 0) {
        Serial.println("Calibration failed. No valid samples.");
        return;
    }

    float acc_x_avg = acc_x_sum / valid_samples;
    float acc_y_avg = acc_y_sum / valid_samples;
    float acc_z_avg = acc_z_sum / valid_samples;

    float expected_x = 0;
    float expected_y = 0;
    float expected_z = 0;

    float abs_x = fabs(acc_x_avg);
    float abs_y = fabs(acc_y_avg);
    float abs_z = fabs(acc_z_avg);

    if (abs_x >= abs_y && abs_x >= abs_z) {
        expected_x = (acc_x_avg >= 0) ? 1.0f : -1.0f;
    } else if (abs_y >= abs_x && abs_y >= abs_z) {
        expected_y = (acc_y_avg >= 0) ? 1.0f : -1.0f;
    } else {
        expected_z = (acc_z_avg >= 0) ? 1.0f : -1.0f;
    }

    offsets.acc_x_offset = acc_x_avg - expected_x;
    offsets.acc_y_offset = acc_y_avg - expected_y;
    offsets.acc_z_offset = acc_z_avg - expected_z;

    offsets.gyro_x_offset = gyro_x_sum / valid_samples;
    offsets.gyro_y_offset = gyro_y_sum / valid_samples;
    offsets.gyro_z_offset = gyro_z_sum / valid_samples;

    Serial.println("Calibration done.");
    Serial.print("Accel offsets: ");
    Serial.print(offsets.acc_x_offset, 4); Serial.print(", ");
    Serial.print(offsets.acc_y_offset, 4); Serial.print(", ");
    Serial.println(offsets.acc_z_offset, 4);

    Serial.print("Gyro offsets: ");
    Serial.print(offsets.gyro_x_offset, 4); Serial.print(", ");
    Serial.print(offsets.gyro_y_offset, 4); Serial.print(", ");
    Serial.println(offsets.gyro_z_offset, 4);
}

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println();
    Serial.println("ESP32-S3 MPU6050 Calibration Test");

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

    calibrateMpu6050();

    Serial.println("MPU6050 initialization done");
    Serial.println();
}

void loop() {
    ImuRawData raw;

    if (readMpuRawData(raw)) {
        ImuData unit = convertRawData(raw);
        ImuData calibrated = applyCalibration(unit);

        Serial.print("CAL | ");
        Serial.print("acc_x_g: "); Serial.print(calibrated.acc_x_g, 3);
        Serial.print(" | acc_y_g: "); Serial.print(calibrated.acc_y_g, 3);
        Serial.print(" | acc_z_g: "); Serial.print(calibrated.acc_z_g, 3);
        Serial.print(" | gyro_x_dps: "); Serial.print(calibrated.gyro_x_dps, 3);
        Serial.print(" | gyro_y_dps: "); Serial.print(calibrated.gyro_y_dps, 3);
        Serial.print(" | gyro_z_dps: "); Serial.println(calibrated.gyro_z_dps, 3);
    } else {
        Serial.println("Failed to read MPU6050 data.");
    }

    delay(500);
}
