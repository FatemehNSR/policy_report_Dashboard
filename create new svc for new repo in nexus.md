با توجه به خروجی‌ات، Nexus تو داخل Kubernetes نصب شده و برای Docker Registry قبلی یک Service جداگانه دارد:

- `nexus-nexus-repository-manager` → پورت UI برابر `32081`
- `nexus-nexus-repository-manager-docker-8082` → پورت Docker Registry برابر `32082`

پس بهتر است برای Repository جدید `docker-policy-reporter` هم یک Service مستقل بسازیم، نه اینکه Serviceهای موجود را ویرایش کنیم.

ساختار نهایی:

Nexus Pod — nexus-nexus-repository-manager

Docker Registry فعلی

8082 → 32082

Policy Reporter Registry

8083 → 32083

## مرحله ۱ — ایجاد Docker Hosted Repository در Nexus

در پنل Nexus از مسیر `Administration → Repositories → Create repository` نوع `docker (hosted)` را انتخاب کن.

تنظیمات:

```
Name: docker-policy-reporter

Online: Enabled

HTTP Connector: Enabled
HTTP Port: 8083

HTTPS Connector: Disabled

Blob Store: default
Deployment Policy: Disable redeploy
```

بعد روی `Create repository` کلیک کن.

نکته: پورت `8083` باید آزاد باشد. این پورت توسط Nexus درون همان Pod استفاده خواهد شد.

## مرحله ۲ — بررسی Selector مربوط به Nexus

قبل از ساخت Service، باید مطمئن شویم Service جدید به همان Pod وصل می‌شود.

این دستور را اجرا کن:

```
kubectl get svc \
  nexus-nexus-repository-manager-docker-8082 \
  -n nexus \
  -o jsonpath='{.spec.selector}{"\n"}'
```

برای اینکه Selector دقیقاً مطابق Service فعلی باشد، پیشنهاد می‌کنم Service جدید را از روی همان Service بسازیم، نه اینکه Labelها را حدس بزنیم.

## مرحله ۳ — ایجاد Service با NodePort جدید

ابتدا بررسی کن که NodePort پیشنهادی قبلاً استفاده نشده است:

```
kubectl get svc -A | grep 32083
```

اگر خروجی خالی بود، فایل زیر را بساز:

```
nano nexus-policy-reporter-svc.yaml
```

محتوا:

```
apiVersion: v1
kind: Service
metadata:
  name: nexus-nexus-repository-manager-docker-8083
  namespace: nexus
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: nexus-repository-manager
    app.kubernetes.io/instance: nexus
  ports:
    - name: docker-8083
      protocol: TCP
      port: 8083
      targetPort: 8083
      nodePort: 32083
```

مهم: مقدار `selector` بالا نمونه است. اگر خروجی مرحله قبل متفاوت بود، حتماً همان Selector واقعی Service فعلی را جایگزین کن.

حالا اجرا کن:

```
kubectl apply -f nexus-policy-reporter-svc.yaml
```

## مرحله ۴ — بررسی Service

```
kubectl get svc -n nexus
```

انتظار داریم:

```
nexus-nexus-repository-manager                8081:32081/TCP
nexus-nexus-repository-manager-docker-8082    8082:32082/TCP
nexus-nexus-repository-manager-docker-8083    8083:32083/TCP
```

سپس:

```
kubectl get endpoints \
  nexus-nexus-repository-manager-docker-8083 \
  -n nexus
```

باید Endpoint با آدرس Pod و پورت `8083` دیده شود.

در نهایت:

```
curl -i http://192.168.72.60:32083/v2/
```

اگر `200` یا `401` گرفتی، Endpoint به Registry جدید پاسخ داده است. اگر `404`، Timeout یا `Connection refused` دریافت کردی، باید تنظیم Repository Connector و مسیر شبکه را بررسی کنیم.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://help.sonatype.com\&sz=32)

Sonatype Help



### مرحله بعد

وقتی `curl` پاسخ درست داد، سه Image استخراج‌شده را با `ctr` به Nexus جدید Push می‌کنیم و سپس فایل `images-map.tsv` را برای پورت `32083` اصلاح خواهیم کرد.

فعلاً فقط Repository و Service جدید را بساز؛ با این روش نه Service فعلی `32082` تغییر می‌کند و نه Imageهای موجود Kyverno تحت تأثیر قرار می‌گیرند.
