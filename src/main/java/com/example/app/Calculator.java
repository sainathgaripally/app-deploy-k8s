package com.example.app;

public class Calculator {

    public int add(int a, int b) {
        return a + b;
    }

    public int subtract(int a, int b) {
        return a - b;
    }

    public int multiply(int a, int b) {
        return a * b;
    }

    // Deliberately bad method for SonarQube to flag (unused & bad practice)
    public void badMethod() {
        String unused = "This variable is never used!";
        if (1 == 1) {
            System.out.println("Unnecessary condition detected!");
        }
    }
}
