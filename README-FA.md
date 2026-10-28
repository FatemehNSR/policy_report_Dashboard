# نصب آفلاین Policy Reporter (نسخه Helm Chart 2.24.0)

## ۱. آماده‌سازی روی GitHub
محتویات این پوشه را در یک GitHub repository قرار بده. از تب Actions، workflow به نام `Policy Reporter Offline Bundle (K8s 1.25)` را Run کن. Artifact خروجی را دانلود کن و ZIP متعلق به GitHub را Extract کن؛ داخلش `policy-reporter-offline-bundle.tar.gz` است.

بسته شامل Helm Chart، تمام Docker imageهای استخراج‌شده از `helm template` در TARهای جداگانه، لیست mapping، و checksum است. تعداد Imageها را از `images-map.tsv` بخوان؛ ثابت فرض نکن.

## ۲. انتقال به محیط آفلاین
`tar -xzf policy-reporter-offline-bundle.tar.gz -C policy-reporter-bundle` را اجرا کن. فایل `post-renderer.py` را هم از همین repository به همان پوشه منتقل کن.

## ۳. بارگذاری و Push به Docker hosted Nexus
حتماً تأیید کن پورت 32082 به Docker Hosted Repository مدنظر متصل است. توجه کن مسیر تصویر `policy-reporter/` داخل Registry یک path است، نه نام Nexus repository.

روی میزبان دارای Docker (با تنظیم insecure registry برای HTTP) و Credential معتبر:

```bash
docker login 192.168.72.60:32082
while IFS=$'\t' read -r src tarfile dst; do
  docker load -i "images/$tarfile"
  docker tag "$src" "$dst"
  docker push "$dst"
done < images-map.tsv
```

## ۴. نصب با Helm موجود روی سرور آفلاین
اگر Helm روی سرور نصب نیست، Helm v3 binary را جداگانه به محیط انتقال بده؛ این Bundle خود Helm executable را ندارد.

```bash
kubectl create namespace policy-reporter --dry-run=client -o yaml | kubectl apply -f -
chmod +x post-renderer.py
export POLICY_REPORTER_IMAGE_MAP="$PWD/images-map.tsv"
helm template policy-reporter ./policy-reporter-2.24.0.tgz -n policy-reporter -f offline-values.yaml --post-renderer ./post-renderer.py > preview.yaml
# Confirm no ghcr.io references left:
grep -E '^[[:space:]]*image:' preview.yaml
helm upgrade --install policy-reporter ./policy-reporter-2.24.0.tgz \
  -n policy-reporter -f offline-values.yaml --post-renderer ./post-renderer.py --wait --timeout 5m
kubectl get pods,svc -n policy-reporter
kubectl port-forward -n policy-reporter svc/policy-reporter-ui 8080:8080
```

در مرورگر روی همان ماشین که port-forward را اجرا کردی: `http://localhost:8080`.

## نکات
- `post-renderer.py` و `offline-values.yaml` باید با Bundle منتقل شوند. فایل values در پوشه Repository اصلی است؛ آن را کنار Chart کپی کن.
- این روش Imageها را از Manifest رندرشده استخراج می‌کند و اجازه نمی‌دهد Image فهرست‌نشده در زمان Helm install استفاده شود.
- روی Nodeهای Kubernetes باید دسترسی HTTP به Nexus در containerd تنظیم شده باشد. این مسیر جدید `policy-reporter/...` است؛ خود repository Docker Hosted همان است که NodePort 32082 می‌دهد.
- برای محیط حساس UI را فعلاً فقط با port-forward در شبکه مدیریت نمایش بده. اتصال عمومی بدون Auth توصیه نمی‌شود.
- Compatibility نسخه Chart و imageها باید با dry-run و اجرای واقعی در آزمایشگاه تأیید شود. این نسخه از شاخه قدیمی v2 انتخاب شده، نه آخرین v3.
