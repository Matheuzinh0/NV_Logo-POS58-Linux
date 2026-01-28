import os
import time
import sys
import io
from escpos.printer import Usb
from pdf2image import convert_from_bytes

# Autor Matheus Sousa

# Config
VENDOR_ID = 0x0416
PRODUCT_ID = 0x5011
PIPE_PATH = "/tmp/printer_pipe" # dir pipe
LOGO_PATH = "/opt/logoV1.bmp" #dir logo

def main():
    # Fila
    if os.path.exists(PIPE_PATH):
        try: os.remove(PIPE_PATH)
        except: pass
    try:
        os.mkfifo(PIPE_PATH)
        os.chmod(PIPE_PATH, 0o666)
    except Exception as e:
        print(f"erro: {e}")
        sys.exit(1)

    print(f"loading . monitor: {PIPE_PATH}")

    while True:
        try:
            # data read
            with open(PIPE_PATH, "rb") as pipe:
                data = pipe.read()
            
            if not data: continue

            print(f"work recive ({len(data)} bytes)")

            try:
                # 3. Conect USB port
                p = Usb(VENDOR_ID, PRODUCT_ID, timeout=0, in_ep=0x81, out_ep=0x01)

                # detach kernel 
                try:
                    if p.is_kernel_driver_active(0):
                        p.detach_kernel_driver(0)
                except Exception: pass
                
                # logo printer
                p.set(align='center')
                if os.path.exists(LOGO_PATH):
                    p.image(LOGO_PATH)
                p.text("\n") # space
                
                #PDF -> RAW
                # signature verification
                if data.startswith(b'%PDF'):
                    print("detect format. convert image...")
                    
                    try:
                        # convert pdf(bytes) to image PIL
                        # dpi=200 for a compromise between quality and speed of thermal printing
                        images = convert_from_bytes(data, dpi=200)
                        
                        for i, img in enumerate(images):
                            print(f"print page {i+1} of pdf...")
                            # the lib escpos acept object PIL image()
                           
                            p.image(img) 
                            p.text("\n") # space
                            
                    except Exception as e_convert:
                        print(f"erro in conversion to pdf: {e_convert}")
                        p.text("erro in renderization .\n")
                
                else:
			#
                    print("format text or raw detected.")
                    p.set(align='left')
                    p._raw(data)
                
                # end
                p.cut()
                p.close()
                print("sucess")

            except Exception as e_usb:
                print(f"erro USB: {e_usb}")
                try: p.close()
                except: pass

        except Exception as e:
            print(f"general erro: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
