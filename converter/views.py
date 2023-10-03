from django.http import JsonResponse
from decimal import Decimal

ExchangeRATES = {
    "GBP": {"EUR": Decimal("1.13"), "USD": Decimal("1.25")},
    "USD": {"EUR": Decimal("0.91"), "GBP": Decimal("0.80")},
    "EUR": {"GBP": Decimal("0.89"), "USD": Decimal("1.10")},
}
def converter(request):
    from_currency = request.GET.get("from_currency")
    to_currency = request.GET.get("to_currency")
    amount = Decimal(request.GET.get("amount"))

    if from_currency == to_currency:
        converted_amount = amount
    elif from_currency in ExchangeRATES and to_currency in ExchangeRATES[from_currency]:
        rate = ExchangeRATES[from_currency][to_currency]
        converted_amount = amount * rate
    else:
        return JsonResponse({
            "error": f"One or both of the provided currencies are not supported: {from_currency}/{to_currency}"
        }, status=400)

    return JsonResponse({
        "from_currency": from_currency,
        "to_currency": to_currency,
        "amount": amount,
        "converted_amount": converted_amount,
    })
