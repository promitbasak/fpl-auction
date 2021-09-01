from django.db import models
from django.conf import settings


class PlayerType(models.Model):
    # GKP, MID, FWD, DEF
    fpl_id = models.IntegerField()
    position = models.CharField(max_length=4, unique=True)
    position_verbose = models.CharField(max_length=20)
    squad_select = models.IntegerField(null=True, blank=True)
    squad_min_play = models.IntegerField(null=True, blank=True)
    squad_max_play = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.position}"


class PlayerStatus(models.Model):
    # status: n: unavailable temporary, d: illness, a: active, s: suspended, u: not in league, i: injured
    status = models.CharField(max_length=2, unique=True)
    status_verbose = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.status}"



class Team(models.Model):
    fpl_id = models.IntegerField()
    fpl_code = models.IntegerField(unique=True)
    name = models.CharField(max_length=25)
    short_name = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.name}"


class Manager(models.Model):
    name = models.CharField(max_length=20)
    team_name = models.CharField(max_length=50)
    total_bid = models.FloatField(null=True, blank=True)
    total_points = models.FloatField(null=True, blank=True, default=0.0)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class Player(models.Model):
    fpl_code = models.IntegerField()
    fpl_id = models.IntegerField()
    element_type = models.ForeignKey(PlayerType, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    second_name = models.CharField(max_length=50, null=True, blank=True)
    web_name = models.CharField(max_length=25)
    photo = models.CharField(max_length=20, null=True, blank=True)
    now_cost = models.FloatField()
    base_cost = models.FloatField()
    minutes = models.FloatField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    status = models.ForeignKey(PlayerStatus, on_delete=models.SET_NULL, null=True, blank=True)
    total_points = models.IntegerField(null=True, blank=True)
    goals_scored = models.IntegerField(null=True, blank=True)
    assists = models.IntegerField(null=True, blank=True)
    clean_sheets = models.IntegerField(null=True, blank=True)
    own_goals = models.IntegerField(null=True, blank=True)
    penalties_saved = models.IntegerField(null=True, blank=True)
    penalties_missed = models.IntegerField(null=True, blank=True)
    yellow_cards = models.IntegerField(null=True, blank=True)
    red_cards = models.IntegerField(null=True, blank=True)
    saves = models.IntegerField(null=True, blank=True)
    bonus = models.IntegerField(null=True, blank=True)
    form = models.FloatField(null=True, blank=True)
    selected_by_percent = models.FloatField(null=True, blank=True)
    base_bid = models.FloatField()
    current_bid = models.FloatField(null=True, blank=True)
    bought = models.BooleanField(blank=True, default=False)
    bought_by = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.second_name}"


class PlayerGameWeek(models.Model):
    gw = models.IntegerField()
    now_cost = models.FloatField(null=True, blank=True)
    minutes = models.FloatField()
    gw_points = models.IntegerField(null=True, blank=True)
    goals_scored = models.IntegerField(null=True, blank=True)
    assists = models.IntegerField(null=True, blank=True)
    clean_sheets = models.IntegerField(null=True, blank=True)
    own_goals = models.IntegerField(null=True, blank=True)
    penalties_saved = models.IntegerField(null=True, blank=True)
    penalties_missed = models.IntegerField(null=True, blank=True)
    yellow_cards = models.IntegerField(null=True, blank=True)
    red_cards = models.IntegerField(null=True, blank=True)
    saves = models.IntegerField(null=True, blank=True)
    bonus = models.IntegerField(null=True, blank=True)
    current_bid = models.FloatField(null=True, blank=True)
    bought_by = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.player.web_name}_{self.gw}"



class ManagerGameWeek(models.Model):
    gw = models.IntegerField()
    total_bid = models.FloatField(null=True, blank=True)
    gw_points = models.FloatField(null=True, blank=True, default=0.0)
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.manager.name}_{self.gw}"



class TransferHistory(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    from_manager = models.ForeignKey(Manager, on_delete=models.CASCADE, null=True, blank=True, 
                                     related_name="from_transfer")
    to_manager = models.ForeignKey(Manager, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name="to_transfer")
    time = models.DateTimeField(auto_now=True, null=True, blank=True)
    bid = models.FloatField(null=True, blank=True)
    # 1: buy, 2. sell, 3. transfer
    type = models.IntegerField()

    def __str__(self):
        return f"{self.from_manager.name}_{self.to_manager.name}_{self.type}"


class Deadlines(models.Model):
    start_time = models.DateTimeField()
    gw = models.IntegerField()
    finished = models.BooleanField(blank=True, default=False)