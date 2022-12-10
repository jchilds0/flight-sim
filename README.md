# flight-sim
A flight simulator controlled using torsion and curvature. 
Built using the panda3D graphics library

# Background

A curve $\gamma$ is a map from $\mathbb{R}$ to $\mathbb{R}^3$. We assume the curve 
is unit speed to simplify the formulas, $|\gamma'(s)| = 1$. Then define the tangent
vector T by $T(s) = \gamma'(s)$. Similarily define the normal vector N, as the unit 
vector in the direction of $T'(s)$. Finally define $B(s)$ as the unit vector in 
the direction of $T(s) \times N(s)$, where $\times$ is the cross product in 
$\mathbb{R}^3$. Finally the curvature $ \kappa $ at a point $\gamma(s)$ is defined 
as the length of T'(s), $\kappa(s) = |T'(s)|$. And the torsion $\tau$ at a point 
$\gamma(s)$ is defined $- N(s) \cdot B'(s)$, where $\cdot$ is the dot product.

The triple (T(s), N(s), B(s)) is called the Frenet-Serre Frame and forms an orthogonal 
basis for $\mathbb{R}^3$. The quantities also satisfy a system of differential equation 
called the [Frenet-Serre Formulas](https://en.wikipedia.org/wiki/Frenet%E2%80%93Serret_formulas)

$$ T'(s) = \kappa N(s) $$

$$ N'(s) = - \kappa T(s) + \tau B(s) $$

$$ B'(s) = - \tau N(s) $$

## Mechanics

We start with an initial position $\gamma(0)$, T(0) = (0, 1, 0), N(0) = (1, 0, 0), 
B(0) = (0, 0, 1). Then we add the formula $\gamma'(s) = T(s)$ to the Frenet-Serre 
Formulas, and solving this system numerically we obtain the next position.

## Interpretation

Curvature can be thought of as how much a curve curves, a curve with constant curvature
is a circle of radius $1 / \kappa$. Torsion measures how much $\gamma$ is twisting out
of the 'osculating plane'. A curve with torsion 0 is contained in a plane.

