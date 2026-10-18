from mediscope.visualization.figures import create_figures

if __name__ == "__main__":
    for path in create_figures():
        print(path.with_suffix(".png"))
        print(path.with_suffix(".svg"))
