import math 
import numpy



def conical_helix_length(R, h, N):
    """
    Compute the arc length L of a conical helix on a right circular cone.

    Parameters
    ----------
    R : float
        Base radius of the cone (same units as h).
    h : float
        Height of the cone.
    N : float
        Number of turns the helix makes from apex (z=0) to base (z=h).

    Returns
    -------
    L : float
        Arc length of the conical helix (same units as R and h).
    """

    # Precompute reusable pieces
    R2 = R * R
    h2 = h * h
    denom_sqrt = math.sqrt(R2 + h2)  # sqrt(R^2 + h^2)

    # First term: (1/2) * sqrt(4π^2 N^2 R^2 + R^2 + h^2)
    term1 = 0.5 * math.sqrt(4 * math.pi**2 * N**2 * R2 + R2 + h2)

    # Second term: ((R^2 + h^2) / (4π N R)) * asinh( (2π N R) / sqrt(R^2 + h^2) )
    asinh_arg = (2 * math.pi * N * R) / denom_sqrt
    term2 = ((R2 + h2) / (4 * math.pi * N * R)) * math.asinh(asinh_arg)

    return term1 + term2

def main():
    print("Conical Helix Arc Length Calculator")
    print("-----------------------------------")
    print("Provide cone dimensions and number of turns.")
    print("Units can be anything (meters, feet, etc.),")
    print("as long as R and h use the same units.\n")

    # Get user input
    R = float(input("Base radius R: "))
    h = float(input("Height h: "))
    N = float(input("Number of turns N: "))

    L = conical_helix_length(R, h, N)

    print("\nResults:")
    print(f"  Arc length L = {L:.4f} (same units as R and h)")

    # Optional: if you treat inputs as meters, show feet too
    L_feet = L * 3.28084
    print(f"  If R and h were in meters, L ≈ {L_feet:.2f} ft")


if __name__ == "__main__":
    main()