from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `lupus_skin_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `symptom_type` VARCHAR(16) NOT NULL COMMENT 'RASH: RASH\nORAL_ULCER: ORAL_ULCER\nHAIR_LOSS: HAIR_LOSS',
    `log_date` DATE NOT NULL,
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_lupus_sk_users_b213a5b4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-LUPUS-001 — SLE 특이 피부 증상 기록 (순수 저장, 해석 없음).';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `lupus_skin_logs`;"""


MODELS_STATE = (
    "eJztXW1z4jgS/isuPs1WZebAQIDU1VU5iZPhlpccJnu7O0y5hC3AGyOzfplZbmv++0myjb"
    "EtO0BIsIm+gJHVwnokS+qnW62/K0tLh6bzSYK2oS0qV8LfFQSWEF8k7lwIFbBaRekkwQVT"
    "k2YFUZ6p49pAc3HqDJgOxEk6dDTbWLmGhXAq8kyTJFoazmigeZTkIeNPD6quNYfuAtr4xp"
    "evONlAOvwLOuHP1ZM6M6Cpxx7V0Ml/03TVXa9oWhe5dzQj+bepqlmmt0RR5tXaXVhok9tA"
    "LkmdQwRt4EJSvGt75PHJ0wX1DGvkP2mUxX/ELRkdzoBnulvV3REDzUIEP/w0Dq3gnPzLR7"
    "HWaDXa9ctGG2ehT7JJaf3wqxfV3RekCAzGlR/0PnCBn4PCGOH2DdoOeaQUeDcLYLPR2xJJ"
    "QIgfPAlhCFgehmFCBGLUcY6E4hL8pZoQzV3SwcVmMwezX6TRzWdp9AHn+onUxsKd2e/jg+"
    "CW6N8jwEZAkldjDxCD7OUEsFat7gAgzpUJIL0XBxD/owv9dzAO4r+V4YAN4pZIAshHhCv4"
    "RTc090IwDcf9WkxYc1AktSYPvXScP81t8D70pV+TuN70htcUBctx5zYthRZwjTEmQ+bsae"
    "vlJwlToD19B7aupu5YopWVN31rKS6TKQCBOcWK1JjUL5hEHh06oKcmF5qeO7V4OIdTrJnl"
    "2pif0eTSEcV6vSVW65ftZqPVararm1kmfStvurnu3pMZJ9Y3n5+C4BIY5j5j50agnKNnY5"
    "fBs5E9djZSQ+cCOAuoqyvgON8tm9Ffs7FkiJYT1ZrY3mVOEtvZcxK5FweWfu+BZpi/nBCK"
    "u3RMMbtjiqmOiWus+8N7GkEZeUuKYhc/EkAaTKEZSZ8Yz0pf6slXAvmcoDvZ/+V/Vw7A+X"
    "IHmC8zUb5Mgjw1bHehg3Ua5lsMDrujbsskwMXjNHSNJfxELorZbXPwu5XGcgKfFa4dVHFv"
    "m2Z1RTZGSblyvtS12i7DYi17VKwl+xtZoh36Soeyb4dl5V4eyCOpV0m/1cGdKyG4mCDpcT"
    "zs9vuPA/x+R9eHvOO1XV7yWvZbXku95oaj4rWv8Y2B/bVlmRCgjPXotlwC9ykWfC3gN2vV"
    "Y7/i18NhL6YZXXcTa87BY/9axvBSdHEmw40tReOY6kuDQX88C2ko9oaI7qv0nARSEziual"
    "pzFqi3wdTCRjUumTcrkYsdQA56YDEmpnG3Lytjqf8Qw5lMV+SOSFPXidTUKmBTiPDf7viz"
    "QH4Kvw/9EWpb99/kG/9eIc8EPNdSkfUdd9vtaofJYVKcj7EhgVYFDEomvyHjkkdoyFNMor"
    "gO+hCZ66AflaRlgy6f27DeSj+wYeOSvGFP2rD04fcg96IO8IQLMKE+hyqGy1tCgkx6AgwK"
    "uft5BE3gsgn/gMP7OSzwNiivmE3/I+zPYWrUBSJwdMOBwIEvRISwmrd+SSXGAni6QafkF6"
    "IhkXJ61rzEUCyhbmi0mkfoGf1NYSVGhCoVhrs+Qv8I3hQpKLHcPcVZL1eutVS1BdSejgCO"
    "4pd3Q4orNzL+O2SqDoZG98yXjrH+W2QqQWklBgY/n4qXAfj/XghJD0xHtJwyg+GtPEd1ng"
    "x0hJenRwpTcFnle3P2MsZG8NmG86SubGtmmCymKBAfIji28Mdu89UIl/kQFVlUtXvH+QqY"
    "0HZVB7ouKfMIEIXzlkQKVqJyy4PTnrb89HqfYdhnKgXZVv5IKZkGi+bjmvu/VFzD9fuvY3"
    "m2BlXLngNk/C9qXG9qGtQauobArnxNOAh8qTgucD2ngtO/YFXYtICO807XKnFQ8FO3mI+v"
    "3KHgVA4Fm4be1dKzESiniUfcyR1LzHHHEtPuWGSw39f8vS1TUihfwzWQwKKugLvYF8uNUD"
    "nBbO7UL5s5/bKZ7pfBIMxE8nn7YyT9hhbIB3lw2x3cMyyQwZ0rIbiYoIfR8EZWFD9xcz1B"
    "t0NikySfE3QndXvy7ZXgfx9kndzNfzPHfTPlvbnw0BMG2mN5cGZObQmp5+e4QiyjjuOTvd"
    "Wl2euRXUeKrOVMKceMV3EtTqzsUtgqS2CamZ00LX1QPz0FtH5HrYuty00fJT/yuqfSl3q9"
    "dB+Ftm3Z6hI6DlYJ0giO4V8Z6KUED+qXxTLlyr+OYyahlGv2xizUGw7uw+xJf+3EAMrNre"
    "dglePm1jNt2BSflGQA1H31+owCSja5vIGunzJyZzdCugXuLBsac/QzXKc0g2zCs5iIZ9F3"
    "ONkG3zdMU1bHwlXFFYS+49aNpNxIt3Llx2l2A32GwHQX956hwwqDO9y+fZHHGi5oRnVOch"
    "Zsj9AZ8Xmvtvs0c9zMHjRLO1AeT13MYUAyNMQTsB7HVArru+iE9WyVsJ7SCCN3DtWvPGMD"
    "WrZOw5Z+Q0YpTSUVVq9x8MiswtkMaq66tJDhWjbT7Ja9yze7hFNt+q38c+YhjSAvTD3DdA"
    "3kfCJ/+K/XaZejbQWOmdmNGXTctQlVA82sfXp/WpL3fGbPDxyBHG+5BDZje1Y2xAxRjjET"
    "Y8p9MibDnOEkEuHjx+Hjh244mgmMJUvnyu7YcamyrEY4F8gpo4O5wALF3wg90jPCcGw5rO"
    "dH41C3neSf1bgrI/k/H2+7ivyxWq39o1oVhYknVmsN/KW1OtWJB7Qq/pyCVgOnNKEukB+g"
    "jT8bukZyVYGGPy9BJ5TQWs02ydWY1fBnu0lEtI6GRfTLZvtT0iR6mifgMUeK6yIUdGAM4e"
    "F7mZNlnDpIwUi6EkbSBCkkOoFyWGiC429b1g0wR5aD56QwnkB6PstaKyQlXxipoFBGREag"
    "AmSxAMpeTIX5uUWVr6LOfRXFLapn17DprZfUOnVIu8YleeiAE4cOOMwcXlrLzolN4NzsHZ"
    "i9i2nq3mx+ZkVW3toYnRNbObYN+3l9e3A3+ngz7D/0uljfbUS67nQ604iuWyP6a7vWxCna"
    "jCrBWofouh1AdN3gfpX+wJotEdFnbeEDfkCI9I8Wnnp+SqvYb/WnXKsurlYNtH19lyOJsn"
    "DBiVB+jR305ctGdjC/Rkpfhi4zHGq2QSOSOII9o1ALn1cxXHC18Cy0B77q5KtOvurMNfds"
    "b9vPMPkkdvY/Y/bZji2wh+2HRNIklpcdrC5as0EWhdVpg6wc621qe9F1/Fmr13wLDBWv4v"
    "t6U2+TpA4Rb7VIXr1JbvjrR73ZaAgfWLabqTjrCDW66NQYK9lyPDJfBxd3Hbyy4RzhgW+t"
    "vmy3KqucN/QDGgTzdFK9pFtRB3Qr6sNIvh9IgzHZrOpfTdD1SJaU8Z0s+1tbYz+xRE8aDP"
    "ztrcFVMexUNkTAVI3lChj2knkOSW5IWJY4Dw2bOKYAroBraIeDzC6Aw5wIaoyIqyxxTl5g"
    "pc/az/OQKcwNjEwDo257cxWYJrTne2GclOPwsu231tKyp4ZuuAbLwzMb35QgB5gbyN8VE8"
    "IN5OfQsOktx4VguM5Hh3uRa+5zXFgYP/CVmbDXbo3X4cFezG1thVDOoLbiQZafYbYS4Z33"
    "4rW2vYlTxA0hjGJ+woTlaWp5hBLQaVJbpFRSs6VTXknLJare8hk481Rc5ul9HVj3Kmf+Ue"
    "1MM4FzMG0XL+HUbuHKWB4Nu7dXQnAxQfRUq6Hy+PAwkhWFsneppAnCH92+1JNGXXJE1vav"
    "CbruDnvD++7NlRBeTdBAkci/0K9DKD1xF1O6mG1KF1OmdMNRDfQHzHBKeO6Ep5go55i4qz"
    "rXxLnCxjXxd9mw3FWdu6pzpyHuNHTmTkOMc5gY5Ar7tKZsgiXcJ5s6MGpHluVm/Msurjjb"
    "+6+pR/msiX/Upk2BpmmhQ860rtFCfF/0luZ757Q0/5NIwno12NPN9MWpVqetSCTundNqZD"
    "kUlbEWzGM0wpcYt6K/MTd5UAZnf07F/myahLkmYYO8LXP2J8FjOfUbYBA72cG/t0RKNtcf"
    "LeDgDLjG3GP0qkzUtiTeK2hLy0b4/1THNWYzBB1HZZ4znglhpvw7PSThDwuXrDrfoWkSWA"
    "BWLfcK+5Ulz/fMJLQqZrAvYJhrVcc90dDw8zO8nTL7MUv0vY4JnDXlrCkn1zhr+k4atqD+"
    "S5xs42Rb5fRkW/JcbwbTxjj6O5tmY587vhvHpvzWf0iyU+F+NRrYsEOIqapWS/BWmkZ2ve"
    "nVyzjj9Emw8Rg8M8FcxU04n0ObEFtTsdMQgn8SaZiHGXVL6kDCfcFL6nekTWnhswx3p6I+"
    "KPeJKi4rRl8I3MzBC7KX1siSPVXU6HKpjOkXi9HN83fUsQrgjjhcBzrDpTI3TPO1Ml8rZ8"
    "dQC0zHkgltV4Gu69c1HU+NlS931bwxSgMiojq+zP7m6foODvhaR6tRky1dndbERmi/Dbzx"
    "WfbdmAO/H5JcpPbhGl3DdvyVbrOhkR/TaHWrdbDIwdEvyl8nviAv7oKc2lTdBZ4rF5a5z+"
    "FvacF3agyjQJD/gJqHxy+o6mC9t1WbJf9O8UwbWw/pns+U8k6xDXwBDkKUKftOcfQXKAec"
    "wJ4SLMtmr7e2JxqOChGp7r5URVzwDSmKzfKAMxScoeBWWt6w52OlPR9ViEeZKGWUCT9+hK"
    "loC6h77AiqySwXeUyTH2LCVJ0g9/6BJhrC89FIg8ANflR9ckgdMV9qWrQ7oF1rEg4FaO1q"
    "yKQEWwE6WsPPvElpk9D9JE9+lNRTPxfneorL9YS93QcrhfVuARVShZw6psJ1bzi8Vcd4or"
    "0SousJehx1B3KQHl1PkPybrMq/Sv0rIbyaIOnhYYjx68sk/sLWjwnqDv4t34y7w8GVsLlM"
    "vn8Zbf7KQVLDhtj/ML+05LlvNuHOvtzZl2sbXI18Jw3LQyTwEAncE4V7opy5J0oPTEfQ8Y"
    "FI8QHRzYs8JgCjr9o03x4cQE+6Tjg+7+aS0Wo3aSDHyCUjUrFjfszUs0KsEcW8rncSor7i"
    "TU7u81X5DEKgiA/J2YHisgMudNy9VcmY0LlrkbSyhguXbO4kB6FQqCzW3jcI7fkNmKwwBt"
    "lAbgTKCeLxT6e04QzaEC89VBsglhtCNpYM0ZJQHa8NKmeKOFPECQXOFL2ThuVMEWeKOFPE"
    "maJzZ4q8lecoTwbK2Nwfu3+RyxeRnKqDs+65rb/3+PCobBMySk8me3LEKaVjWg16/myd7L"
    "PR29Xk/vlEBEmxpvncCw07STfVt0DzghZBHT1qNf84XO2S3GpkOY0U4aE4J1RcTiiMY/Ei"
    "h5FEGaf2FxlJyucrgXxO0HAk9dTH3o08uhKi6wn6LHVHam+oKFfC5jL5Ap3G64OHFeWeHl"
    "x/52oe1995w1a4/s71d66/c/39TPX3H/8HI1Uulg=="
)
