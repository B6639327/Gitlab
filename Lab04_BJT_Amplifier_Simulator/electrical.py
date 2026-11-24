"""DC Circuit Calculator.

This program performs quick calculations for basic direct-current circuits
using Ohm's law and electrical power formulas.
"""

from __future__ import annotations

from typing import Sequence


def _require_non_zero(name: str, value: float) -> float:
    """Validate that a numeric input is not zero for division operations."""
    if value == 0:
        raise ValueError(f"{name} cannot be zero.")
    return float(value)


def calculate_voltage(current: float, resistance: float) -> float:
    """Return voltage using V = I x R."""
    return float(current) * float(resistance)


def calculate_current(voltage: float, resistance: float) -> float:
    """Return current using I = V / R."""
    _require_non_zero("Resistance", resistance)
    return float(voltage) / float(resistance)


def calculate_resistance(voltage: float, current: float) -> float:
    """Return resistance using R = V / I."""
    _require_non_zero("Current", current)
    return float(voltage) / float(current)


def calculate_power(
    voltage: float,
    current: float | None = None,
    resistance: float | None = None,
    formula: str = "voltage_current",
) -> float:
    """Return electrical power.

    Supported formulas:
    - voltage_current: P = V x I
    - current_resistance: P = I^2 x R
    - voltage_resistance: P = V^2 / R
    """
    voltage = float(voltage)
    formula = formula.lower()

    if formula == "voltage_current":
        if current is None:
            raise ValueError("Current is required for the voltage-current formula.")
        return voltage * float(current)

    if formula == "current_resistance":
        if current is None:
            raise ValueError("Current is required for the current-resistance formula.")
        if resistance is None:
            raise ValueError("Resistance is required for the current-resistance formula.")
        resistance = _require_non_zero("Resistance", resistance)
        return (float(current) ** 2) * resistance

    if formula == "voltage_resistance":
        if resistance is None:
            raise ValueError("Resistance is required for the voltage-resistance formula.")
        resistance = _require_non_zero("Resistance", resistance)
        return (voltage ** 2) / resistance

    raise ValueError(
        "Unsupported formula. Use 'voltage_current', 'current_resistance', or 'voltage_resistance'."
    )


def total_resistance_series(resistors: Sequence[float]) -> float:
    """Return total resistance for a series circuit."""
    return sum(float(value) for value in resistors)


def total_resistance_parallel(resistors: Sequence[float]) -> float:
    """Return total resistance for a parallel circuit."""
    if not resistors:
        raise ValueError("At least one resistor is required.")

    reciprocal_sum = sum(1 / float(value) for value in resistors if float(value) != 0)
    if reciprocal_sum == 0:
        raise ValueError("Parallel circuit total resistance is undefined.")
    return 1 / reciprocal_sum


def _prompt_float(prompt: str) -> float:
    while True:
        raw_value = input(prompt).strip()
        try:
            return float(raw_value)
        except ValueError:
            print("Please enter a valid number.")


def main() -> None:
    """Launch the command-line DC circuit calculator."""
    print("DC Circuit Calculator")
    print("====================")
    print("1. Calculate voltage (V = I × R)")
    print("2. Calculate current (I = V / R)")
    print("3. Calculate resistance (R = V / I)")
    print("4. Calculate power (P = V × I)")
    print("5. Calculate total resistance in series")
    print("6. Calculate total resistance in parallel")
    print("7. Exit")

    while True:
        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            current = _prompt_float("Current (A): ")
            resistance = _prompt_float("Resistance (Ω): ")
            result = calculate_voltage(current, resistance)
            print(f"Voltage = {result:.2f} V")

        elif choice == "2":
            voltage = _prompt_float("Voltage (V): ")
            resistance = _prompt_float("Resistance (Ω): ")
            result = calculate_current(voltage, resistance)
            print(f"Current = {result:.2f} A")

        elif choice == "3":
            voltage = _prompt_float("Voltage (V): ")
            current = _prompt_float("Current (A): ")
            result = calculate_resistance(voltage, current)
            print(f"Resistance = {result:.2f} Ω")

        elif choice == "4":
            voltage = _prompt_float("Voltage (V): ")
            current = _prompt_float("Current (A): ")
            result = calculate_power(voltage, current)
            print(f"Power = {result:.2f} W")

        elif choice == "5":
            count = int(_prompt_float("How many resistors? "))
            values = []
            for index in range(1, count + 1):
                values.append(_prompt_float(f"Resistor {index} (Ω): "))
            print(f"Total series resistance = {total_resistance_series(values):.2f} Ω")

        elif choice == "6":
            count = int(_prompt_float("How many resistors? "))
            values = []
            for index in range(1, count + 1):
                values.append(_prompt_float(f"Resistor {index} (Ω): "))
            print(f"Total parallel resistance = {total_resistance_parallel(values):.2f} Ω")

        elif choice == "7":
            print("Goodbye.")
            break

        else:
            print("Invalid option. Please choose 1 to 7.")

        print("\n" + "-" * 30)


if __name__ == "__main__":
    main()
