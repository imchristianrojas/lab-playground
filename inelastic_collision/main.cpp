#include <SFML/Graphics.hpp>
#include <vector>
#include <iostream>
#include <optional> // for std::optional (SFML 3 events)

struct Particle {
    float mass;
    float velocity;
    float x_pos;
};

class Simulation {
public:
    void addParticle(const Particle& p) { particles.push_back(p); }

    void reset() {
        particles = initial;
        hasCollided = false;
    }

    void setInitial(const std::vector<Particle>& init) {
        initial = init;
        particles = init;
        hasCollided = false;
    }

    void update(float dt) {
        for (auto &p : particles) {
            p.x_pos += p.velocity * dt;
        }

        if (particles.size() >= 2 && !hasCollided) {
            auto &p1 = particles[0];
            auto &p2 = particles[1];
            if (p1.x_pos >= p2.x_pos) {
                float vf = handleCollision(p1, p2);
                Particle combined = {
                    p1.mass + p2.mass,
                    vf,
                    0.5f * (p1.x_pos + p2.x_pos)
                };
                particles.clear();
                particles.push_back(combined);
                hasCollided = true;
            }
        }
    }

    const std::vector<Particle>& getParticles() const { return particles; }

private:
    float kineticEnergy(const Particle& p) {
        return 0.5f * p.mass * p.velocity * p.velocity;
    }

    float totalKineticEnergy(const Particle& a, const Particle& b) {
        return kineticEnergy(a) + kineticEnergy(b);
    }

    float handleCollision(Particle &p1, Particle &p2) {
        float init_momentum = (p1.mass * p1.velocity) + (p2.mass * p2.velocity);
        float final_velocity = init_momentum / (p1.mass + p2.mass);
        (void)totalKineticEnergy(p1, p2); // kept for potential metrics later
        (void)kineticEnergy(p1);
        return final_velocity;
    }

    std::vector<Particle> particles;
    std::vector<Particle> initial;
    bool hasCollided = false;
};

int main() {
    Particle p1 = {5.0f, 10.0f, 0.0f};
    Particle p2 = {2.0f, 0.0f, 20.0f}; 
    Simulation sim;
    sim.setInitial({p1, p2});


    //Used LLM on this shoutout claude shouldve learned and read documents and tutorials but i was hungry and football was on ;O
    //
    sf::RenderWindow window(sf::VideoMode({900u, 240u}), "Inelastic Collision");
    window.setFramerateLimit(60);

    const float pixelsPerMeter = 10.f;
    const float baselineY = 140.f;
    const float startX = 50.f;
    bool playing = true;
    sf::Clock clock;

    //I DO NOT KNOW WHAT ANY OF THIS MEANS...YET
    while (window.isOpen()) {
        // SFML 3: pollEvent returns std::optional<sf::Event>
        while (const std::optional event = window.pollEvent()) {
            // Window closed
            if (event->is<sf::Event::Closed>()) {
                window.close();
                continue;
            }

            // Key pressed
            if (const auto* keyPressed = event->getIf<sf::Event::KeyPressed>()) {

                if (keyPressed->scancode == sf::Keyboard::Scancode::Space){
                    playing = !playing;
                } else if (keyPressed->scancode == sf::Keyboard::Scancode::R)                {
                    sim.reset();
                    clock.restart();
                }
            }
        }

        float dt = playing ? clock.restart().asSeconds() : 0.f;
        if (playing) sim.update(dt);

        window.clear(sf::Color(20, 24, 28));

        sf::RectangleShape line(sf::Vector2f(800.f, 2.f));
        line.setPosition(sf::Vector2f(startX, baselineY + 15.f));
        line.setFillColor(sf::Color(120, 120, 120));
        window.draw(line);

        //this is me with some help
        for (size_t i = 0; i < sim.getParticles().size(); ++i) {
            const auto &p = sim.getParticles()[i];
            float x = startX + p.x_pos * pixelsPerMeter;
            float radius = 10.f + p.mass;

            sf::CircleShape shape(radius);
            shape.setOrigin(sf::Vector2f(radius, radius));
            shape.setPosition(sf::Vector2f(x, baselineY - radius * 0.2f));
            shape.setFillColor(i == 0
                                ? sf::Color(70, 180, 255)
                                : sf::Color(255, 140, 70));
            window.draw(shape);
        }

        window.display();
    }

    return 0;
}
