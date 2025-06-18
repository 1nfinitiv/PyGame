if self.is_defender:
    # Логика защитников (без изменений)
    closest_enemy = None
    min_dist = float('inf')
    for enemy in game.units:
        if not enemy.is_defender:
            dist = math.sqrt((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2)
            if dist < min_dist:
                min_dist = dist
                closest_enemy = enemy
    if closest_enemy:
        if min_dist <= self.attack_range:
            self.last_attack += dt
            if self.last_attack >= self.attack_cooldown:
                self.last_attack = 0
                closest_enemy.health -= self.attack_damage
                if closest_enemy.health <= 0:
                    game.units.remove(closest_enemy)
        else:
            angle = math.atan2(closest_enemy.y - self.y, closest_enemy.x - self.x)
            self.x += self.speed * math.cos(angle)
            self.y += self.speed * math.sin(angle)