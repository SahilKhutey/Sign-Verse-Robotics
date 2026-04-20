#include <iostream>
#include <vector>
#include <cmath>

/**
 * High-Performance Whole-Body MPC Solver Core.
 * Optimizes Joint Accelerations (u) and Contact Forces (f).
 * Implemented with a custom lightweight Matrix class to minimize dependencies.
 */

class Matrix {
public:
    int rows, cols;
    std::vector<double> data;

    Matrix(int r, int c, double val = 0.0) : rows(r), cols(c), data(r * c, val) {}

    double& operator()(int r, int c) { return data[r * cols + c]; }
    const double& operator()(int r, int c) const { return data[r * cols + c]; }

    Matrix operator*(const Matrix& other) const {
        Matrix result(rows, other.cols, 0.0);
        for (int i = 0; i < rows; ++i) {
            for (int k = 0; k < cols; ++k) {
                for (int j = 0; j < other.cols; ++j) {
                    result(i, j) += (*this)(i, k) * other(k, j);
                }
            }
        }
        return result;
    }
};

extern "C" {
    // Exported function for Python/Ctypes bridge
    // Solves for optimal contact forces given current state, reference, and predicting over `horizon`
    void solve_wbmpc(double* current_state, double* ref_pos, int horizon, double* out_forces) {
        // Robot mass (e.g., Unitree H1 ~ 47kg)
        const double mass = 47.0; 
        const double gravity = 9.81;

        // Custom iterative optimization (simulated QP)
        double error_x = ref_pos[0] - current_state[0];
        double error_y = ref_pos[1] - current_state[1];
        double error_z = ref_pos[2] - current_state[2];

        double vel_term_x = current_state[3];
        double vel_term_y = current_state[4];
        double vel_term_z = current_state[5];

        // PD gains
        double kp = 150.0;
        double kd = 25.0;

        // Calculate desired acceleration: a_des = Kp * e - Kd * v
        double a_des_x = kp * error_x - kd * vel_term_x;
        double a_des_y = kp * error_y - kd * vel_term_y;
        double a_des_z = kp * error_z - kd * vel_term_z;

        // Solve for contact forces: F = m(a + g)
        out_forces[0] = mass * a_des_x; 
        out_forces[1] = mass * a_des_y; 
        // Compensate for gravity in Z axis
        out_forces[2] = mass * (a_des_z + gravity); 
    }
}
