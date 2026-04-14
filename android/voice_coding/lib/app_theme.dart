import 'package:flutter/material.dart';

class AppSpacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double componentPadding = 14;
  static const double componentGap = 12;
  static const double borderRadius = 12;
}

class AppColors {
  static const Color surface = Color(0xFF3D3B37);
  static const Color background = Color(0xFF000000);
  static const Color inputFill = Color(0xFF2D2B28);
  static const Color textPrimary = Color(0xFFECECEC);
  static const Color textHint = Color(0xFF6B6B6B);
  static const Color primary = Color(0xFFD97757);
  static const Color success = Color(0xFF5CB87A);
  static const Color warning = Color(0xFFE5A84B);
  static const Color error = Color(0xFFE85C4A);
  static const Color divider = Color(0x14FFFFFF);
}

class AppTextStyles {
  static const TextStyle label = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
  );
  static const TextStyle body = TextStyle(
    fontSize: 16,
    color: AppColors.textPrimary,
  );
  static const TextStyle hint = TextStyle(
    fontSize: 13,
    color: AppColors.textHint,
  );
}

ThemeData buildAppTheme() {
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: const ColorScheme.dark(
      primary: AppColors.primary,
      secondary: AppColors.primary,
      surface: Color(0xFF343330),
      error: AppColors.error,
    ),
    scaffoldBackgroundColor: AppColors.background,
    cardColor: const Color(0xFF343330),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.inputFill,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        borderSide: BorderSide.none,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        borderSide: const BorderSide(color: AppColors.primary),
      ),
      hintStyle: const TextStyle(color: AppColors.textHint),
    ),
    textTheme: const TextTheme(
      bodyLarge: TextStyle(color: AppColors.textPrimary, fontSize: 16),
      bodyMedium: TextStyle(color: AppColors.textPrimary, fontSize: 14),
      titleLarge: TextStyle(
        color: AppColors.textPrimary,
        fontSize: 20,
        fontWeight: FontWeight.bold,
      ),
    ),
  );
}
