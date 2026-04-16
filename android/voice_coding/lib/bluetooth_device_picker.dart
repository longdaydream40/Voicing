import 'package:flutter/material.dart';

import 'app_theme.dart';
import 'bluetooth_bridge.dart';

class BluetoothDevicePicker extends StatelessWidget {
  const BluetoothDevicePicker({
    super.key,
    required this.devices,
    required this.selectedAddress,
    required this.onRefresh,
    required this.onOpenSystemSettings,
    required this.onSelectDevice,
  });

  final List<BluetoothDeviceInfo> devices;
  final String? selectedAddress;
  final VoidCallback onRefresh;
  final VoidCallback onOpenSystemSettings;
  final ValueChanged<BluetoothDeviceInfo> onSelectDevice;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('选择蓝牙设备', style: AppTextStyles.label),
            const SizedBox(height: AppSpacing.sm),
            const Text(
              '请先在系统蓝牙设置中完成配对，App 只显示已配对设备。',
              style: AppTextStyles.hint,
            ),
            const SizedBox(height: AppSpacing.md),
            if (devices.isEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(AppSpacing.componentPadding),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
                ),
                child: const Text(
                  '暂无已配对设备',
                  style: AppTextStyles.body,
                ),
              )
            else
              ...devices.map((device) {
                final isSelected = device.address == selectedAddress;
                return Container(
                  margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
                  ),
                  child: ListTile(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
                    ),
                    title: Text(device.name, style: AppTextStyles.body),
                    subtitle: Text(device.address, style: AppTextStyles.hint),
                    trailing: isSelected
                        ? const Icon(
                            Icons.check_circle,
                            color: AppColors.success,
                          )
                        : const Icon(
                            Icons.chevron_right,
                            color: AppColors.textHint,
                          ),
                    onTap: () => onSelectDevice(device),
                  ),
                );
              }),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: onRefresh,
                    child: const Text('刷新列表'),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: FilledButton(
                    onPressed: onOpenSystemSettings,
                    child: const Text('系统蓝牙设置'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
