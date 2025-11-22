# Inelastic Collision Visualizer

## Motivation

At work today I was reviewing my kinematics from physics. I relearned how to derive the basic motion equations using calculus and fundamental relationships such as:

- \( v = \frac{dx}{dt} \)
- \( a = \frac{dv}{dt} \)

I also revisited how to solve for unknowns in **inelastic collisions** using conservation of momentum. While working through the math, I thought it would be cool to build a small simulation to *visualize* these collisions and show their outcomes — final velocity, combined mass, and changes in kinetic energy.

## Method

The simulation models a simple **1-dimensional perfectly inelastic collision**:

- Two masses, \( m_1 \) and \( m_2 \), move along the same line.
- \( m_1 \) begins with velocity \( v_1 \) and moves to the right.
- \( m_2 \) begins with velocity \( v_2 \) (or at rest) and moves to the left.
- When they collide, they stick together and move as a combined mass.

After collision, the final velocity is computed using **conservation of momentum**:

\[
v_f = \frac{m_1 v_1 + m_2 v_2}{m_1 + m_2}
\]

The simulation visualizes the motion, collision, and post-collision movement using SFML.

## Results

From the visualization, you can observe:

- The initial motion of both masses.
- The final motion of the combined mass.
- **Total momentum remains conserved**, as expected:
  \[
  m_1 v_1 + m_2 v_2 = (m_1 + m_2)v_f
  \]
- **Kinetic energy decreases**, which is characteristic of perfectly inelastic collisions.

This provides an intuitive link between the equations and the physical behavior.

## Conclusion

- The simulation correctly demonstrates **momentum conservation**.  
- It also shows that **kinetic energy is not conserved** in a perfectly inelastic collision.  
- The final velocity corresponds to the **mass-weighted average** of the initial velocities, not a simple arithmetic average unless the masses are equal.

Overall, this project helped solidify the connection between the equations of motion, conservation laws, and real physical behavior.

## Future Work

Planned improvements include:

- User-input parameters (masses, velocities, positions, acceleration)
- Displaying energy and momentum numerically on screen
- Multi-mass sequential collisions
- Higher-dimensional simulations
- Support for additional forces (springs, friction, etc.)
- Real-time energy and momentum graphs

## Disclaimer

I did the heavy lifting for the physics derivations and logic.  
However, I **did** use an LLM to help with visualization code and structuring the simulation.
 

## My little sim lmaooo

![My Preview](images/inelastic_simScreen.png)
