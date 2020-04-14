import logging
from InspectorQuickstart import InspectorQuickstart

def main():
    logging.basicConfig(level=logging.INFO)
    print("Hello Inspector")
    spector = InspectorQuickstart()
    spector.subscribe_to_sns()
    assement_run = spector.start_run()

if __name__== "__main__":
    main()