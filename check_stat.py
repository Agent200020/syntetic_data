import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

# ----------------------------- 1. Исходные данные -----------------------------
# Это данные, представляющие тепловую карту активности за неделю (по дням и часам)
heatmap = [
    [66,74,62,111,181,238,451,573,570,489,454,351,436,465,603,609,614,513,440,382,255,170,135,64],
    [68,60,61,147,163,237,467,585,587,499,435,378,443,475,571,580,574,548,488,342,249,201,125,48],
    [59,54,48,114,160,200,487,591,567,448,419,348,388,443,554,517,558,477,458,319,244,169,116,58],
    [59,54,50,105,172,229,421,536,575,462,389,330,397,421,580,581,544,456,456,333,216,191,110,68],
    [71,81,57,138,203,267,488,589,574,471,488,348,467,459,596,599,607,545,506,340,224,185,128,55],
    [61,57,63,93,174,215,418,543,565,448,568,362,412,404,560,597,549,496,467,326,440,375,202,54],
    [55,47,50,105,162,235,395,589,544,452,508,295,390,437,569,548,538,486,408,323,436,368,225,56]
]

heatmap = np.array(heatmap, dtype=float)

# Это наши веса для разных часов дня
base_hour_weights = [
    1, 1, 1,     # 0-2
    2, 3, 4,     # 3-5
    8, 10, 10,   # 6-8
    8, 7, 6,     # 9-11
    7, 8, 10,    # 12-14
    10, 10, 9,   # 15-17
    8, 6, 4,     # 18-20
    3, 2, 1      # 21-23
]

weights = np.array(base_hour_weights, dtype=float)

# ----------------------------- 2. Масштабируем данные -----------------------------
scaled_base = np.zeros_like(heatmap)  # Массив для хранения масштабированных данных

for day in range(heatmap.shape[0]):
    day_sum = heatmap[day].sum()         # Суммируем все значения за день
    weight_sum = weights.sum()          # Суммируем все веса
    scale_k = day_sum / weight_sum      # Определяем коэффициент для масштабирования
    scaled_base[day] = weights * scale_k  # Масштабируем по часам

# ----------------------------- 3. Отклонения -----------------------------
# считаем отклонения
diff = heatmap - scaled_base

df_real = pd.DataFrame(heatmap)
df_scaled = pd.DataFrame(scaled_base)
df_diff = pd.DataFrame(diff)

print("\n=== ОРИГИНАЛЬНАЯ ТЕПЛОВАЯ КАРТА ===")
print(df_real.round(2))

print("\n=== ОЖИДАЕМОЕ (Масштабированное) ===")
print(df_scaled.round(2))

print("\n=== ОТКЛОНЕНИЯ (реальные - ожидаемые) ===")
print(df_diff.round(2))

# ----------------------------- 5. Статистическая проверка -----------------------------

# 5.1. Тест Колмогорова-Смирнова
ks_statistic, ks_p_value = stats.ks_2samp(heatmap.flatten(), scaled_base.flatten())

print(f"\n=== Результат теста Колмогорова-Смирнова ===")
print(f"KS Statistic: {ks_statistic:.4f}, p-value: {ks_p_value:.4f}")

if ks_p_value < 0.05:
    print("Распределения отличаются, гипотеза отвергается.")
else:
    print("Нет оснований для отказа от гипотезы: распределения похожи.")

# 5.2. Тест хи-квадрат
observed, bins = np.histogram(diff.flatten(), bins=20)
expected = np.full_like(observed, observed.sum() / len(observed))  # Ожидаемое распределение — равномерное

# Нормализуем частоты для корректной работы теста
observed = observed / observed.sum()
expected = expected / expected.sum()

# Проводим тест хи-квадрат
chi2_statistic, chi2_p_value = stats.chisquare(observed, expected)

print(f"\n=== Результат теста хи-квадрат ===")
print(f"Xi2 Statistic: {chi2_statistic:.4f}, p-value: {chi2_p_value:.4f}")

# Интерпретация результата теста:
if chi2_p_value < 0.05:
    print("Распределение отклонений отличается от ожидаемого.")
else:
    print("Распределение отклонений похоже на ожидаемое.")

# ----------------------------- 6. Визуализация отклонений -----------------------------
# Строим тепловую карту, чтобы наглядно увидеть, где отклонения наибольшие
plt.figure(figsize=(14, 5))

plt.imshow(diff, cmap="bwr", aspect="auto")  
plt.colorbar(label="Отклонение (реальные - ожидаемые)")

plt.title("Отклонения по дням и часам")  # Заголовок
plt.xlabel("Часы (0-23)")  # Подпись для оси X
plt.ylabel("Дни")  # Подпись для оси Y

plt.xticks(np.arange(24), np.arange(24))
plt.yticks(np.arange(diff.shape[0]), [f"День {i+1}" for i in range(diff.shape[0])])

plt.tight_layout()
plt.show()
