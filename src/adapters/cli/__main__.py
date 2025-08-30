import argparse
from ...domain.models import QRCodeSpec
from ...application.service import QRCodeService
from ...infrastructure.factory import default_encoders
from ...infrastructure.storage.localfs import LocalFileStorage

def main():
    p = argparse.ArgumentParser(description="Generate QR codes (PNG/SVG).")
    p.add_argument("data", help="Text/URL to encode")
    p.add_argument("-o", "--out", help="Output filepath (e.g. out.png)", default=None)
    p.add_argument("--fmt", choices=["png","svg"], default="png")
    p.add_argument("--bg", choices=["white","transparent"], default="white")
    p.add_argument("--ec", choices=["L","M","Q","H"], default="M")
    p.add_argument("--box", type=int, default=10)
    p.add_argument("--border", type=int, default=4)
    p.add_argument("--fill", default="black")
    p.add_argument("--dir", default=".")
    args = p.parse_args()

    svc = QRCodeService(encoders=default_encoders(), storage=LocalFileStorage(args.dir))
    spec = QRCodeSpec(
        data=args.data, error=args.ec, box_size=args.box, border=args.border,
        fill_color=args.fill, background=args.bg, fmt=args.fmt
    )
    if args.out:
        path = svc.generate_and_save(spec, args.out)
        print(path)
    else:
        data = svc.generate_bytes(spec)
        print(f"Generated {args.fmt} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
