"""Text content of the project report. Markup: **bold**, *italic*. All numbers come from results/metrics and logs/."""

PRIMARY_TITLE = "EcoSort AI: Real-Time Waste Classification Using Vision-Language Models"

ABSTRACT = [
    "Sorting waste correctly at the point of disposal improves recycling quality, keeps compost clean and protects sanitation workers, "
    "especially from medical items such as syringes and tablet strips. This project presents **EcoSort AI**, a real-time computer-vision "
    "system that classifies an item shown to a camera into one of four disposal categories: biodegradable, recyclable, non-recyclable "
    "and medical waste, and answers \"Unknown\" when it is not confident enough.",
    "Four model generations were built and compared. Version 1 used classical image processing (Otsu segmentation and 149 hand-crafted "
    "shape, colour and texture features) with SVM and Random Forest classifiers and reached 73.1% on six classes. Version 2, a fine-tuned "
    "MobileNetV2, reached 95.7% on clean dataset photographs but only 45.1% (ten classes) and 75.5% (four categories) on real landfill "
    "photographs. Version 3, a ConvNeXt-Tiny attempt, was stopped early. Version 4, the final system, passes each image through the "
    "frozen SigLIP 2 vision-language encoder and trains a small logistic-regression classifier on its 768-dimensional embedding.",
    "The final model was trained on 21,445 de-duplicated images from four sources (Garbage Classification, RealWaste, TrashNet and "
    "Wikimedia Commons medical photographs) using leakage-controlled 70/15/15 splits. On the 3,308-image test set it achieves "
    "**98.73% accuracy and 0.9875 macro-F1** (training 99.60%, validation 98.75%), 96.7% on real landfill photographs, 97.7% recall "
    "for medical waste with no ordinary item sent to the medical bin (0 of 2,998), and about 21 ms of model time per image on a "
    "laptop GPU. A confidence threshold of 0.59, chosen on the validation split, defers 1.0% of images to manual sorting and raises "
    "accuracy on the answered images to 99.1%. The system is delivered as a web application with live camera, image upload and a "
    "Teach function that stores corrected photographs for retraining.",
    "**Keywords:** waste classification, computer vision, vision-language model, SigLIP 2, transfer learning, medical waste, real-time system.",
]

ABBREVIATIONS = [
    ("AI", "Artificial Intelligence"), ("API", "Application Programming Interface"), ("CNN", "Convolutional Neural Network"),
    ("CV", "Computer Vision"), ("dHash", "Difference Hash (perceptual image hash)"), ("EMA", "Exponential Moving Average"),
    ("EXIF", "Exchangeable Image File Format"), ("F1", "Harmonic mean of precision and recall"), ("GPU", "Graphics Processing Unit"),
    ("HSV", "Hue, Saturation, Value (colour space)"), ("HTTP", "Hypertext Transfer Protocol"), ("JSON", "JavaScript Object Notation"),
    ("LBP", "Local Binary Pattern"), ("MD5", "Message-Digest Algorithm 5 (file hash)"), ("ML", "Machine Learning"),
    ("MPS", "Metal Performance Shaders (Apple GPU back end)"), ("RF", "Random Forest"), ("RGB", "Red, Green, Blue"),
    ("SDG", "Sustainable Development Goal"), ("SigLIP", "Sigmoid Loss for Language-Image Pre-training"),
    ("SVM", "Support Vector Machine"), ("UI", "User Interface"), ("ViT", "Vision Transformer"), ("VLM", "Vision-Language Model"),
    ("YOLO", "You Only Look Once (object detector)"),
]

B = []  # blocks

# =============================================================== CHAPTER 1
B += [("h1", "1", "INTRODUCTION"),
 ("h2", "1.1", "INTRODUCTION TO PROJECT", "Introduction to Project"),
 ("p", "Waste segregation is the first and most important step of waste management. When biodegradable material, recyclable material, "
       "non-recyclable material and hazardous medical items are mixed, recycling plants receive contaminated material, compost becomes unusable "
       "and sanitation workers are exposed to injury and infection. Sorting by hand is slow, inconsistent and unpleasant, so there is a clear "
       "case for a camera-based system that tells a person which bin an item belongs in."),
 ("p", "This project builds **EcoSort AI**, a real-time waste classification system. A user shows an item to a camera, or uploads a photograph, "
       "and the system answers with one of four disposal categories: **biodegradable** (food, peels, leaves), **recyclable** (paper, notes, books, "
       "cardboard, plastic bottles, metal cans, glass), **non-recyclable** (thermocol, wrappers, contaminated packaging, cloth, leather, shoes) or "
       "**medical waste** (tablet strips, syringes, masks, gloves, bandages). When the model is not confident enough it answers \"Unknown\" so that a "
       "person can decide instead of the system guessing."),
 ("p", "The work follows an evidence-driven path. A classical computer-vision pipeline was built first, as taught in the course units, and "
       "then replaced step by step as measurements showed its limits: a fine-tuned convolutional network looked excellent on clean dataset photographs "
       "but failed on real landfill photographs, which led to a larger multi-source dataset and finally to a vision-language backbone (SigLIP 2) "
       "with a small trained classifier. The final system is delivered as a web application with a live camera view, image upload and a \"Teach\" "
       "button that lets users correct mistakes."),
 ("p", "The remainder of this report is organised as follows. Chapter 2 surveys related work and the research gaps. Chapter 3 describes the "
       "methodology, functional requirements and architecture. Chapter 4 presents the results, tests and discussion. Chapter 5 concludes and lists future "
       "enhancements. The appendix contains the main source code."),

 ("h2", "1.2", "PROBLEM STATEMENT AND DESCRIPTION", "Problem Statement and Description"),
 ("p", "**Problem statement.** Design and build a computer-vision system that, from a single camera image of a waste item, names the correct disposal "
       "category (biodegradable, recyclable, non-recyclable or medical) in real time, remains accurate on real-world photographs rather than only on clean "
       "dataset images, and declines to answer when it is unsure."),
 ("p", "The problem has five parts, each of which became a design requirement:"),
 ("ul", ["**Real-world robustness.** Public datasets mostly contain a single object on a plain background. A sorting system meets clutter, dirt, "
         "shadows, mixed materials and unusual lighting.",
         "**Disposal categories, not materials.** Most datasets label the material (paper, plastic, glass). Users need the bin: for example cloth "
         "and leather are non-recyclable although they are not plastic or glass, and paper is recyclable.",
         "**Medical waste.** Syringes, tablet blister strips, masks and gloves must never be mixed with ordinary waste, yet no medical-waste "
         "image dataset could be found for direct download in this project's search.",
         "**Knowing when it does not know.** A confident wrong answer is worse than a refusal, so the system needs a calibrated way to say \"Unknown\".",
         "**Real-time use.** The answer must appear within a fraction of a second so that a live camera view feels instant."]),
 ("p", "**Scope and assumptions.** The system classifies one item at a time, the item shown inside a marked box in the camera view. Detecting and "
       "sorting several items in one frame is left as future work. Accuracy is measured on held-out photographs; a separate test on live camera frames "
       "is listed as the next step."),

 ("h2", "1.3", "MOTIVATION", "Motivation"),
 ("ul", ["**Quality of recycling.** Contamination lowers the value of recyclable material and can cause whole batches to be rejected.",
         "**Safety.** Needles, syringes and used masks hidden in household waste injure and endanger collection workers.",
         "**Access.** A phone or laptop camera is enough; no special sensors or conveyor hardware are needed for a first version.",
         "**An honest research question.** Models that score above 95% on a standard dataset can fall to under 50% on real photographs. Measuring "
         "that gap and closing it is a practical and publishable engineering lesson.",
         "**Fit with the course.** The project exercises image processing (segmentation, morphology, feature extraction), classical machine learning, "
         "deep learning, transfer learning and evaluation, all in one end-to-end system."]),

 ("h2", "1.4", "SUSTAINABLE DEVELOPMENT GOAL OF THE PROJECT", "Sustainable Development Goal of the Project"),
 ("p", "The project supports the United Nations Sustainable Development Goals [26] listed in Table 1.1."),
 ("tbl", "Sustainable Development Goals addressed by the project", ["SDG", "Relevant target", "Contribution of EcoSort AI"],
  [["SDG 11: Sustainable Cities and Communities", "Target 11.6: reduce the adverse environmental impact of cities, including municipal waste management",
    "Helps households and facilities sort waste correctly at the source."],
   ["SDG 12: Responsible Consumption and Production", "Target 12.5: substantially reduce waste generation through prevention, reduction, recycling and reuse",
    "Cleaner recyclable and biodegradable streams make recycling and composting more effective."],
   ["SDG 3: Good Health and Well-being", "Safe handling of hazardous waste",
    "Flags medical items (syringes, tablet strips, masks, gloves) so they are kept out of household waste."]],
  [2400, 3000, 2910], ["l", "l", "l"]),
]

# =============================================================== CHAPTER 2
B += [("h1", "2", "LITERATURE SURVEY"),
 ("h2", "2.1", "OVERVIEW OF THE RESEARCH AREA", "Overview of the Research Area"),
 ("h3", "2.1.1", "From hand-crafted features to deep learning"),
 ("p", "Early image classifiers separated the problem into segmentation, feature extraction and classification. Objects were isolated with thresholding "
       "(for example Otsu's method [15]), described with shape moments [16], colour histograms and texture descriptors such as local binary patterns [17], and "
       "classified with support vector machines [18] or random forests [19]. These methods need little data and run quickly, but every stage depends on the "
       "previous one, and a failed segmentation corrupts all features."),
 ("p", "Convolutional neural networks learn features directly from pixels. After large-scale training on ImageNet [5], architectures such as ResNet [6], "
       "MobileNetV2 [7], EfficientNet [9] and ConvNeXt [8] became the standard backbones for image classification, and fine-tuning them on a small task (transfer "
       "learning) became the usual way to build practical classifiers."),
 ("h3", "2.1.2", "Vision transformers and vision-language models"),
 ("p", "Vision Transformers (ViT) [4] split an image into patches and process them with self-attention. Vision-language models such as CLIP [3] and SigLIP [2] "
       "train an image encoder and a text encoder together on very large collections of web images with captions, so that an image and its description "
       "have similar embeddings. SigLIP 2 [1] improves this recipe with better semantic understanding and localisation. Two properties matter for waste "
       "sorting: the image features transfer well to photo styles never seen in the task data, and the text encoder can score an image against written "
       "descriptions without any task-specific training (zero-shot classification)."),
 ("h3", "2.1.3", "Waste-image datasets"),
 ("p", "TrashNet [12] contains 2,527 photographs of single items on a white board in six material classes. The Kaggle Garbage Classification dataset [24] "
       "provides about 15,500 mostly web-sourced images in twelve classes, including clothes, shoes, batteries and three glass colours. RealWaste [11] "
       "contains 4,752 photographs taken at a real landfill in nine classes, with the clutter and variation of real conditions. TACO [13] provides "
       "litter photographed in context with detailed annotations for detection. No image dataset dedicated to medical waste such as syringes and tablet strips "
       "was found for direct download in this project's search."),
 ("h3", "2.1.4", "Confidence and rejection"),
 ("p", "A classifier outputs probabilities, but a sorting system must also decide when not to answer. Choosing a confidence threshold on a validation set, "
       "so that the answers that are kept meet a target accuracy, is a simple and effective form of selective classification, and it is the approach used here."),

 ("h2", "2.2", "EXISTING MODELS AND FRAMEWORKS", "Existing Models and Frameworks"),
 ("p", "Table 2.1 summarises the families of approaches used for waste classification and the framework-level tools used to build them."),
 ("tbl", "Existing approaches to image-based waste classification", ["Approach", "Representative work", "Strengths", "Limitations"],
  [["Hand-crafted features + SVM / Random Forest", "Early TrashNet baselines [12]; Otsu [15], Hu moments [16], LBP [17], SVM [18], Random Forest [19]",
    "Small data, fast, transparent", "Depends on clean segmentation; weak on clutter"],
   ["Fine-tuned CNN (transfer learning)", "ResNet [6], MobileNetV2 [7], EfficientNet [9], ConvNeXt [8]; CNN waste classifiers such as [14]",
    "High accuracy on dataset photos; mature tooling", "Accuracy can drop sharply on unseen photo styles"],
   ["Object detectors", "YOLO [10] with litter datasets such as TACO [13]", "Locates several items in a frame", "Needs box annotations; item category is coarse"],
   ["Vision transformers and vision-language models", "ViT [4], CLIP [3], SigLIP [2], SigLIP 2 [1]",
    "Robust, transferable features; zero-shot text queries", "Larger models; need care to run in real time"]],
  [1900, 2600, 1900, 1910], ["l", "l", "l", "l"]),
 ("p", "**Frameworks used in this project.** PyTorch [22] and torchvision for deep learning, Hugging Face Transformers [23] to load SigLIP 2, scikit-learn [21] "
       "for SVM, Random Forest and logistic regression, and OpenCV [27] for image processing. All are open source."),

 ("h2", "2.3", "LIMITATIONS IDENTIFIED FROM LITERATURE SURVEY (RESEARCH GAPS)", "Limitations Identified from Literature Survey (Research Gaps)"),
 ("ol", ["**Clean-photo bias.** Standard benchmarks such as TrashNet contain single objects on plain backgrounds. Reported accuracy on them does not predict "
         "behaviour on real photographs. This project measured the effect directly: the same CNN fell from 95.7% to 45.1% (Section 4.2.2).",
         "**Material labels instead of disposal rules.** Datasets label material, while users need a bin. The mapping from material to bin is rarely made explicit.",
         "**Little public medical-waste image data.** No dataset of syringes, tablet strips, masks and gloves could be found for direct download in this project's search, so photographs had to be assembled from freely licensed sources.",
         "**Duplicate images across datasets.** Overlap between datasets can silently inflate test accuracy. In this project 2,358 of the 2,527 TrashNet images were found "
         "to be already present in the Garbage Classification dataset.",
         "**Rejection is rarely evaluated.** Few waste classifiers report what happens when the model is uncertain.",
         "**Retraining is costly.** Large fine-tuned networks are slow to retrain when new local items appear, which discourages adapting to a new site."]),

 ("h2", "2.4", "RESEARCH OBJECTIVES", "Research Objectives"),
 ("ol", ["Build a classifier for four disposal categories (biodegradable, recyclable, non-recyclable, medical) from a single camera image.",
         "Measure how well models trained on clean photographs transfer to real landfill photographs, and choose a model that transfers well.",
         "Assemble a multi-source, de-duplicated dataset with splits that prevent leakage between training and test images.",
         "Add medical-waste recognition using freely licensed photographs, and verify that ordinary items are not sent to the medical bin.",
         "Provide a reliable \"Unknown\" option using a threshold chosen on validation data.",
         "Deliver a real-time web application with live camera, upload and a Teach function for continuous improvement."]),

 ("h2", "2.5", "PRODUCT BACKLOG (KEY USER STORIES WITH DESIRED OUTCOMES)", "Product Backlog (Key user stories with Desired outcomes)"),
 ("tbl", "Product backlog of key user stories", ["ID", "User story", "Desired outcome", "Priority", "Status"],
  [["US1", "As a user, I show an item to the camera and see its category.", "Category and confidence appear within a fraction of a second.", "High", "Done"],
   ["US2", "As a user, I upload one or more photographs.", "Each photograph gets a category.", "High", "Done"],
   ["US3", "As a user, I see why the system answered as it did.", "Confidence bars and a \"looks like\" description are shown.", "Medium", "Done"],
   ["US4", "As a user, I want the system to admit when it is unsure.", "Low-confidence items are marked Unknown for manual sorting.", "High", "Done"],
   ["US5", "As a safety officer, I want medical items identified separately.", "Syringes, strips, masks and gloves map to Medical waste.", "High", "Done"],
   ["US6", "As a user, I can correct a wrong answer.", "Corrected photos are saved by category for retraining.", "Medium", "Done"],
   ["US7", "As a user, I see counts for the session.", "A session log shows the number of items per category.", "Low", "Done"],
   ["US8", "As an administrator, I can retrain with new photos.", "Scripts rebuild embeddings and the model.", "Medium", "Done"],
   ["US9", "As a user, I want several items in one frame sorted.", "Detector and tracker find and count each item.", "Medium", "Planned"],
   ["US10", "As a team, we measure accuracy on live camera frames.", "A locked real-world test set from our own camera.", "High", "Planned"],
   ["US11", "As an operator, I want to run on a phone or small device.", "Model exported for edge deployment.", "Low", "Planned"]],
  [560, 2900, 3000, 900, 950], ["c", "l", "l", "c", "c"]),
]

# =============================================================== CHAPTER 3
B += [("h1", "3", "EXECUTION METHODOLOGY"),
 ("h2", "3.1", "OBJECTIVES", "Objectives"),
 ("h3", "3.1.1", "Project objectives"),
 ("ul", ["Classify waste images into four disposal categories with at least 95% accuracy on unseen photographs.",
         "Keep at least 85% accuracy on held-out real landfill photographs.",
         "Send no ordinary item to the medical category, and recognise most medical items.",
         "Respond fast enough for a live camera view (tens of milliseconds of model time).",
         "Defer uncertain items to manual sorting using a validated confidence threshold.",
         "Make the whole pipeline reproducible: fixed seeds, recorded splits, automated tests and version control."]),
 ("h3", "3.1.2", "Methodology overview"),
 ("p", "The project was executed iteratively. Each phase produced a measurable result, and the result decided the next phase (Table 3.1)."),
 ("tbl", "Project phases and the decision each produced", ["Phase", "Work carried out", "Result", "Decision"],
  [["1", "Classical pipeline: Otsu segmentation, 149 features, SVM and Random Forest", "73.1% (6 classes); 64.7% (10 classes)", "Segmentation fails on clutter; move to deep learning"],
   ["2", "Fine-tuned MobileNetV2 on a 6,000-image subset", "95.7% on clean photos", "Test on real photographs before trusting it"],
   ["3", "Add RealWaste landfill photos; de-duplicate; leakage-safe splits", "MobileNetV2: 45.1% (10 classes), 75.5% (4 categories) on landfill photos",
    "Domain shift is the main risk; need a more robust backbone"],
   ["4", "ConvNeXt-Tiny attempt; then SigLIP 2 with a linear classifier", "ConvNeXt stopped at epoch 2 of 15; SigLIP 2: 98.73% test",
    "Select SigLIP 2 + linear classifier"],
   ["5", "Medical photos, Unknown threshold, web application, tests", "Medical recall 97.7%; 0 false medical alarms; 38 passing tests", "Deliver the application"]],
  [600, 2900, 2600, 2210], ["c", "l", "l", "l"]),

 ("h2", "3.2", "FUNCTIONAL DOCUMENT", "Functional Document"),
 ("h3", "3.2.1", "Actors and use cases"),
 ("p", "Two actors use the system. The **user** shows items to the camera or uploads photographs, reads the category, and optionally corrects a wrong answer. "
       "The **administrator** collects the corrected photographs and retrains the model. Table 3.2 lists the functional requirements."),
 ("tbl", "Functional requirements", ["ID", "Requirement", "Acceptance criterion"],
  [["FR1", "Classify an image into one of four categories", "Response contains category, confidence and probability per category"],
   ["FR2", "Return Unknown for low-confidence images", "Confidence below the threshold (0.59) yields Unknown"],
   ["FR3", "Live camera mode with a centre box", "Result updates continuously; label does not flicker"],
   ["FR4", "Upload mode for one or many images", "Each file is classified and shown with a thumbnail"],
   ["FR5", "Explain the answer", "A \"looks like\" description and top matches are shown"],
   ["FR6", "Teach function", "Click saves the current crop under the chosen category"],
   ["FR7", "Session log", "Counts per category and thumbnails are listed"],
   ["FR8", "Retraining scripts", "New photos are included in the next embedding and training run"],
   ["FR9", "Report model quality", "Test metrics are shown in the application"]],
  [700, 3500, 4110], ["c", "l", "l"]),
 ("h3", "3.2.2", "Non-functional requirements"),
 ("tbl", "Non-functional requirements", ["Quality", "Requirement", "Measured"],
  [["Performance", "Model time per image of tens of milliseconds on a laptop GPU", "About 21 ms (20-30 ms after warm-up)"],
   ["Accuracy", "95% or more on unseen photographs; 85% or more on landfill photographs", "98.73%; 96.7%"],
   ["Safety", "No ordinary item sent to the medical category", "0 of 2,998 test items"],
   ["Reproducibility", "Fixed seeds, recorded splits, automated tests", "Seed 42; manifest.csv; 38 tests"],
   ["Usability", "Runs in a browser; camera permission requested by the browser", "Implemented"],
   ["Security", "No access outside the web folder; limits on upload size", "Path traversal blocked; 15 MB limit"]],
  [1700, 4000, 2610], ["l", "l", "l"]),
 ("h3", "3.2.3", "Application programming interface"),
 ("tbl", "HTTP interface of the web server", ["Method and path", "Input", "Output"],
  [["GET /api/info", "none", "Model name, threshold, categories, test metrics, counts of taught photos"],
   ["POST /api/classify", "Image bytes (JPEG or PNG)", "Category, best guess, confidence, probabilities, top matches, time in ms"],
   ["POST /api/teach?category=<name>", "Image bytes", "Saved file name and number of photos in that category"]],
  [2600, 2100, 3610], ["l", "l", "l"]),
 ("h3", "3.2.4", "User interface"),
 ("p", "The web page has three tabs. **Live camera** shows the video with a centre box whose colour follows the predicted category (green biodegradable, blue "
       "recyclable, grey non-recyclable, red medical, amber unknown), the result card, probability bars, the \"looks like\" text, Teach buttons and a session log. "
       "**Upload images** accepts one or many files. **Model and categories** shows the test metrics and the meaning of each category."),

 ("h2", "3.3", "ARCHITECTURE DOCUMENT", "Architecture Document"),
 ("h3", "3.3.1", "System architecture"),
 ("p", "Figure 3.1 shows the real-time path and the teach loop. The browser captures the centre box of the camera frame, compresses it to a 384-pixel JPEG and "
       "sends it to a small Python server. The server computes the SigLIP 2 embedding, the trained classifier converts it to category probabilities, and a confidence "
       "threshold decides between a category and Unknown. The browser smooths the probabilities over frames (weight 0.4 for the newest frame) so that the label does "
       "not flicker. When a user corrects an answer, the photograph is saved by category and is used in the next training run."),
 ("fig", "fig_architecture.png", "System architecture and teach loop", 6.1, "System architecture"),
 ("h3", "3.3.2", "Data architecture"),
 ("p", "Four sources were combined (Table 3.5). Real landfill photographs from RealWaste were included deliberately so that the model is not tuned only to clean photographs."),
 ("tbl", "Data sources", ["Source", "Images used", "Content", "Licence / terms"],
  [["Garbage Classification (Kaggle) [24]", "15,493", "Web photos in 12 folders: battery, biological, cardboard, clothes, three glass colours, metal, paper, plastic, shoes, trash",
    "See Kaggle dataset page"],
   ["RealWaste (UCI) [11]", "4,752", "Photos taken at a real landfill, nine material classes", "CC BY 4.0"],
   ["TrashNet [12]", "169 new", "Single items on a white board; 2,358 of 2,527 images already in Garbage Classification", "See GitHub repository"],
   ["Wikimedia Commons [25]", "1,031", "Medical items: syringes and needles, blister packs, masks, gloves, pill bottles, swabs and bandages, ampoules and vials",
    "Creative Commons, per file"],
   ["Total", "21,445", "Unique images after de-duplication", ""]],
  [2200, 1000, 3600, 1510], ["l", "r", "l", "l"]),
 ("p", "**Preparation pipeline.** Figure 3.2 summarises the steps. Every image has its EXIF rotation corrected, is converted to RGB and is resized so that its shorter "
       "side is 288 pixels. Exact duplicates are found with an MD5 file hash: 2,380 files were removed, including three hashes that appeared under conflicting labels. "
       "Near-duplicates are found with a 256-bit difference hash (dHash): images within a Hamming distance of 20 are grouped (122 groups covering 742 images), and each group "
       "is kept entirely inside one split. The images are then split 70/15/15 into training, validation and test sets, stratified by category at group level with seed 42. "
       "The 1,150 medical photographs were filtered with a zero-shot check that removes drawings, diagrams and documents (1,031 kept) and were split 50/20/30 per item type, "
       "because there are far fewer of them."),
 ("fig", "fig_dataprep.png", "Data preparation pipeline", 6.1, "Data preparation pipeline"),
 ("p", "**Class mapping.** The classifier is trained on fine-grained classes and a fixed rule converts them to categories (Table 3.6): paper, notes and books are recyclable; "
       "cloth, leather and shoes are non-recyclable; only food, leaves, peels and plant matter are biodegradable; batteries are flagged non-recyclable because they need a special "
       "collection point. Leather goods and handkerchiefs have no class of their own and rely on the shoes and clothes images."),
 ("tbl", "Mapping from dataset classes to disposal categories", ["Category", "Dataset classes"],
  [["Biodegradable", "biological (Garbage Classification); Food Organics and Vegetation (RealWaste)"],
   ["Recyclable", "paper, cardboard, plastic, metal, glass (brown, green and white merged), from all photo sources"],
   ["Non-recyclable", "trash and Miscellaneous Trash; clothes and Textile Trash; shoes; battery"],
   ["Medical waste", "Wikimedia photos of syringes and needles, blister packs, masks, gloves, pill bottles, swabs and bandages, ampoules and vials"]],
  [2200, 6110], ["l", "l"]),
 ("tbl", "Number of images per split and category", ["Category", "Train", "Validation", "Test", "Total"],
  [["Biodegradable", "1,284", "274", "274", "1,832"], ["Recyclable", "6,152", "1,267", "1,270", "8,689"], ["Non-recyclable", "6,903", "1,536", "1,454", "9,893"],
   ["Medical", "508", "213", "310", "1,031"], ["Total", "14,847", "3,290", "3,308", "21,445"]],
  [2310, 1500, 1500, 1500, 1500], ["l", "r", "r", "r", "r"]),
 ("fig", "fig_split.png", "Images per split, stacked by category", 4.6, "Stacked bar chart of images per split"),
 ("p", "Figure 3.3 shows the same counts. Medical waste is only 4.8% of the data, so the classifier uses class-balanced weights and macro-F1 is reported next to accuracy."),

 ("h3", "3.3.3", "Classical pipeline (Version 1)"),
 ("p", "The classical pipeline follows the course units. An image is converted to grayscale, smoothed with a 5x5 Gaussian filter and thresholded with Otsu's method. "
       "The mask is cleaned by morphological opening and closing with a 5x5 elliptical element, and the largest connected component is kept as the object (Figure 3.4). "
       "From the object, 149 features are computed: 4 shape values (area, circularity, aspect ratio, extent), 7 log-scaled Hu moments, a 128-bin HSV colour histogram (8x4x4 bins) "
       "and a 10-bin uniform local binary pattern histogram. An RBF-kernel SVM (C = 10) and a Random Forest (300 trees), both class-balanced, are trained on an 80/20 stratified split."),
 ("fig", "fig_pipeline_classical.png", "Classical segmentation pipeline: original, grayscale, Gaussian blur, Otsu mask, after morphology, detected object", 5.0, "Segmentation stages for six waste items"),
 ("h3", "3.3.4", "CNN baseline (Version 2)"),
 ("p", "An ImageNet-pretrained MobileNetV2 [7] was fine-tuned in two phases. In phase 1 only the new last layer was trained for 3 epochs (Adam, learning rate 1e-3). "
       "In phase 2 the whole network was fine-tuned for 4 epochs (Adam [20], learning rate 1e-4). Input size was 224x224 with ImageNet normalisation, batch size 32, and "
       "augmentation by random horizontal flips and rotations of up to 15 degrees. The data were a 6,000-image subset (600 per class, ten classes), split 80/20."),
 ("h3", "3.3.5", "Final model (Version 4): SigLIP 2 with a trained classifier"),
 ("p", "The final model (Figure 3.5) uses the SigLIP 2 base model (google/siglip2-base-patch16-224) [1] as a frozen image encoder. Each image is resized to 224x224 and "
       "normalised to the range -1 to 1, and the encoder returns a 768-number embedding of unit length. A multinomial logistic-regression classifier (scikit-learn [21], L2 "
       "regularisation, C = 20, class-balanced weights) is trained on these embeddings to predict 11 fine-grained classes (the ten material classes plus medical). The category "
       "probabilities are obtained by adding the probabilities of the classes that belong to each category, using the mapping in Table 3.6. Because the mapping is applied after "
       "training, it can be changed without retraining."),
 ("fig", "fig_model.png", "Architecture of the final model", 6.1, "Final model architecture"),
 ("p", "**Text branch.** The same SigLIP 2 model contains a text encoder. Sixty-eight short descriptions (14 biodegradable, 16 recyclable, 19 non-recyclable and 19 medical, "
       "for example \"an empty tablet blister strip\" or \"a used syringe\") are each inserted into five sentence templates (such as \"a photo of {}.\"), encoded once, and averaged. "
       "Comparing an image embedding with these concept embeddings gives the \"looks like: ...\" explanation shown in the application. Used alone, this zero-shot method reaches "
       "83.3% test accuracy; it is reported as a no-training baseline and was not used for the final decision (Section 4.2.3)."),
 ("p", "**Confidence threshold.** A prediction is accepted only if its top category probability is at least 0.59. The threshold is the lowest value between 0.30 and 0.95 for which "
       "the accepted validation predictions are at least 99% correct. It is applied unchanged to the test split."),
 ("h3", "3.3.6", "Training and evaluation protocol"),
 ("p", "All choices (regularisation C, whether to blend in the zero-shot scores, the confidence threshold) were made on the validation split. The test split was used once, at the end. "
       "Table 3.8 lists the settings of the final model."),
 ("tbl", "Settings of the final model", ["Setting", "Value"],
  [["Backbone", "google/siglip2-base-patch16-224, frozen"], ["Input", "224 x 224 RGB, normalised to the range -1 to 1"],
   ["Classifier", "Multinomial logistic regression, L2, class-balanced, maximum 3,000 iterations"],
   ["Regularisation C", "20, chosen from {0.5, 1, 2, 5, 10, 20} on validation macro-F1"],
   ["Targets", "11 fine-grained classes mapped to 4 categories"], ["Unknown threshold", "0.59 (99% accuracy on accepted validation items)"],
   ["Data", "14,847 training / 3,290 validation / 3,308 test images"], ["Random seed", "42"]],
  [2400, 5910], ["l", "l"]),
 ("h3", "3.3.7", "Implementation environment"),
 ("tbl", "Software and hardware environment", ["Component", "Version / detail"],
  [["Language", "Python 3.10.13"], ["Deep learning", "PyTorch 2.14.1, torchvision 0.29.2 (Apple MPS GPU back end)"], ["Vision-language model", "Transformers 5.20.2"],
   ["Machine learning", "scikit-learn 1.7.2"], ["Image processing", "OpenCV 5.0.0, Pillow 12.3.0"], ["Data and plotting", "NumPy 2.2.6, pandas 2.3.3, matplotlib 3.10.9"],
   ["Testing", "pytest (38 automated tests)"], ["Hardware", "Apple-silicon Mac, 16 GB memory"]],
  [2600, 5710], ["l", "l"]),
 ("h3", "3.3.8", "Web application design"),
 ("p", "The server is a Python standard-library HTTP server that serves one HTML page and three JSON endpoints (Table 3.4). One inference runs at a time, guarded by a lock. "
       "The page is plain HTML, CSS and JavaScript. It opens the camera with the browser's own permission prompt, crops the centre box (72% of the displayed height), sends the "
       "crop as a 384-pixel JPEG, and smooths the returned probabilities with an exponential moving average (weight 0.4). The Teach function sends a 512-pixel crop to "
       "/api/teach, which stores it under data/raw/user_captures/<category>/. The next run of the embedding script uses these photographs (80% for training, 20% for validation)."),
]

# =============================================================== CHAPTER 4
B += [("h1", "4", "RESULTS AND DISCUSSIONS"),
 ("h2", "4.1", "PROJECT OUTCOMES", "Project Outcomes"),
 ("p", "The project delivered the following outcomes (Table 4.1):"),
 ("tbl", "Project deliverables", ["Deliverable", "Description"],
  [["Dataset", "21,445 de-duplicated images in four sources, with a recorded leakage-safe split (manifest.csv)"],
   ["Models", "Classical baseline, MobileNetV2 baseline, and the final SigLIP 2 model with its classifier"],
   ["Web application", "Live camera, upload, Teach function, session log and metrics page"],
   ["Scripts", "Data download and preparation, embedding, training, evaluation, figure and report generation"],
   ["Test suite", "38 automated tests covering segmentation, features, datasets, models, splits and the classifier"],
   ["Documentation", "README, data description and this report"]],
  [2200, 6110], ["l", "l"]),
 ("tbl", "Objectives and measured outcomes", ["Objective", "Goal", "Outcome"],
  [["Accuracy on unseen photographs", "95% or more", "98.73% (3,308 test images); macro-F1 0.9875"],
   ["Accuracy on real landfill photographs", "85% or more", "96.7% (690 RealWaste test images)"],
   ["No ordinary item sent to the medical category", "None", "0 of 2,998 ordinary test items; 97.7% of medical items found"],
   ["Real-time response", "Tens of milliseconds", "About 21 ms model time per image"],
   ["Defer uncertain items", "Validated threshold", "0.59: 1.0% deferred; answered items 99.1% correct"]],
  [3300, 1800, 3210], ["l", "l", "l"]),

 ("h2", "4.2", "PERFORMANCE EVALUATION", "Performance Evaluation"),
 ("h3", "4.2.1", "Metrics"),
 ("p", "**Accuracy** is the fraction of images classified correctly. **Precision** of a category is the fraction of images predicted as that category that really belong to it. "
       "**Recall** is the fraction of images of that category that were found. The **F1-score** is the harmonic mean of precision and recall, and **macro-F1** is its average over the "
       "categories, which gives every category equal weight even when categories differ in size. Results on the test split are the final numbers; the validation split was used for tuning."),
 ("h3", "4.2.2", "Baseline models"),
 ("p", "**Classical pipeline.** Table 4.3 shows the results. The Random Forest reached 73.1% on the six TrashNet classes and 64.7% on ten classes. The mask produced by Otsu "
       "thresholding is wrong when the object fills the frame (cardboard), casts a shadow (glass) or sits on a cluttered background, and every feature built on it is corrupted. "
       "Run-to-run differences of one to two points occurred when the file order, and therefore the split, changed."),
 ("tbl", "Version 1: classical pipeline results", ["Dataset", "Classes", "Test images", "Random Forest", "SVM"],
  [["TrashNet", "6", "506", "73.1%", "72.9%"], ["Garbage-10", "10", "1,200", "64.7%", "57.1%"]],
  [2300, 1300, 1700, 1700, 1310], ["l", "r", "r", "r", "r"]),
 ("p", "**MobileNetV2.** Figure 4.1 shows the training loss falling from 1.12 to 0.08 and the held-out accuracy rising to 95.7% over seven epochs. This early version had no separate "
       "validation split, so accuracy was measured on the held-out set after each epoch."),
 ("fig", "fig_mobilenet.png", "MobileNetV2 training loss and held-out accuracy (epochs 1-3 head only, 4-7 whole network)", 6.1, "MobileNetV2 training curves"),
 ("p", "**Domain shift.** When the same MobileNetV2 was applied to the 690 RealWaste test photographs, which it had never seen, accuracy fell to 45.1% on ten classes. Collapsing its "
       "output to the four disposal categories on exactly the same images gives 75.5%, the like-for-like task for comparison with the final model (which, unlike this CNN, was also trained on landfill photographs; see Section 4.5). The per-class recall (Figure 4.2) shows that trash was found "
       "only 4.0% of the time and cardboard 26.6%. The network had learned centred objects on plain backgrounds, not the clutter, dirt and lighting of real photographs. "
       "Accuracy on a clean test set did not predict real-world accuracy."),
 ("fig", "fig_domainshift.png", "MobileNetV2 on clean photographs and on real landfill photographs", 6.1, "MobileNetV2 domain shift"),
 ("p", "**ConvNeXt-Tiny.** A ConvNeXt-Tiny recipe (15 epochs, AdamW, strong augmentation) was started on the multi-source data. After two epochs it reached 93.0% validation accuracy "
       "(macro-F1 0.917) with about 8.5 minutes per epoch, and the run stalled under memory pressure and was stopped. It is not counted as a result."),

 ("h3", "4.2.3", "Final model: tuning on the validation split"),
 ("p", "Validation accuracy and macro-F1 of the logistic-regression classifier increased with the regularisation strength C (Figure 4.3), from 97.66% at C = 0.5 to 98.75% at C = 20. "
       "The curve is still rising at the largest value tried, but the gain from C = 10 to C = 20 is only 0.12 points, so it is flattening."),
 ("fig", "fig_csweep.png", "Validation accuracy and macro-F1 against regularisation strength C", 4.6, "Validation curve over C"),
 ("p", "The zero-shot scores were also blended with the trained classifier for several weights and temperatures. The best blend improved validation macro-F1 by at most 0.002, "
       "which is within noise, and it lowered confidence values. The simpler classifier-only model was therefore selected, and the text branch is kept only for explanations. "
       "On the test split the zero-shot method alone reached 83.3% accuracy (macro-F1 0.818), compared with 98.73% for the trained classifier."),
 ("h3", "4.2.4", "Training, validation and test accuracy"),
 ("tbl", "Accuracy of the final model on each split", ["Split", "Images", "Accuracy", "Macro-F1", "Mean confidence"],
  [["Training", "14,847", "99.60%", "0.9966", "98.4%"], ["Validation", "3,290", "98.75%", "0.9848", "97.9%"], ["Test", "3,308", "98.73%", "0.9875", "98.0%"]],
  [1900, 1600, 1700, 1600, 1510], ["l", "r", "r", "r", "r"]),
 ("p", "The gap between training and test accuracy is 0.87 points, so the classifier is not memorising the training images. Validation and test accuracy agree (98.75% and 98.73%), "
       "which shows that tuning on the validation split did not leak into the test result."),
 ("h3", "4.2.5", "Results by category"),
 ("tbl", "Test precision, recall and F1-score by category", ["Category", "Precision", "Recall", "F1-score", "Images"],
  [["Biodegradable", "0.985", "0.989", "0.987", "274"], ["Recyclable", "0.978", "0.995", "0.987", "1,270"], ["Non-recyclable", "0.993", "0.982", "0.988", "1,454"],
   ["Medical", "1.000", "0.977", "0.989", "310"], ["Macro average", "0.989", "0.986", "0.988", "3,308"]],
  [2310, 1500, 1500, 1500, 1500], ["l", "r", "r", "r", "r"]),
 ("fig", "fig_prf.png", "Test precision, recall and F1-score by category", 5.6, "Bar chart of precision, recall and F1"),
 ("p", "As Figure 4.4 shows, all four categories are between 97.7% and 100% on every measure. Medical waste has precision 1.000: nothing else is ever sent to the medical bin. Its recall is 0.977, "
       "meaning that 7 of 310 medical test images were missed."),
 ("h3", "4.2.6", "Confusion matrix"),
 ("p", "Figure 4.5 shows the confusion matrix on the test split. Of 3,308 images, 42 (1.27%) were wrong. The largest error is 22 non-recyclable items predicted as recyclable (1.5% of that class). "
       "These images have not yet been reviewed one by one, so no cause is claimed. Biodegradable items were almost never confused with recyclable ones (1 of 274). The medical column holds 303 correct "
       "answers and no wrong ones; the 7 missed medical items were predicted recyclable (5) or non-recyclable (2)."),
 ("fig", "fig_confusion.png", "Confusion matrix of the final model on the test split (counts)", 4.6, "Confusion matrix"),
 ("h3", "4.2.7", "Results by data source"),
 ("tbl", "Test accuracy by data source", ["Source", "Test images", "Correct", "Accuracy"],
  [["Garbage Classification", "2,282", "2,277", "99.8%"], ["Medical photographs (Wikimedia)", "310", "303", "97.7%"], ["RealWaste (real landfill)", "690", "667", "96.7%"],
   ["TrashNet", "26", "19", "73.1%"]],
  [3800, 1500, 1500, 1510], ["l", "r", "r", "r"]),
 ("fig", "fig_source.png", "Test accuracy by data source, and the earlier CNN against the final model on the same landfill photographs", 6.1, "Accuracy by source"),
 ("p", "As Figure 4.6 shows, the model is strongest on web-style photographs and a little lower on real landfill photographs, which are the hardest. On the identical 690 landfill photographs and the identical "
       "four-category task, accuracy rose from 75.5% (earlier CNN) to 96.7%, an improvement of 21.2 points that combines a stronger backbone with landfill photographs in the training data (Section 4.5). The TrashNet figure rests on only 26 images (19 correct) after duplicates were "
       "removed and is therefore very uncertain."),
 ("h3", "4.2.8", "Medical waste"),
 ("tbl", "Recall for each medical item type (test photographs)", ["Item type", "Test images", "Found", "Recall"],
  [["Syringes and needles", "110", "110", "100%"], ["Gloves", "26", "26", "100%"], ["Swabs and bandages", "73", "72", "98.6%"], ["Ampoules and vials", "50", "48", "96.0%"],
   ["Masks", "22", "21", "95.5%"], ["Pill bottles", "16", "15", "93.8%"], ["Blister packs (tablet strips)", "13", "11", "84.6%"], ["All medical", "310", "303", "97.7%"]],
  [3600, 1600, 1500, 1610], ["l", "r", "r", "r"]),
 ("fig", "fig_medical.png", "Recall per medical item type", 5.2, "Medical recall per item type"),
 ("p", "No ordinary item was flagged as medical (0 of 2,998), and Figure 4.7 shows the recall for each item type. Blister packs have the lowest recall, but only 13 test photographs exist, so 84.6% is an uncertain estimate. All medical photographs "
       "come from Wikimedia Commons and are cleaner than real hospital waste; a few are mislabelled (for example a gold bar in blister packaging). The Teach function is the way to close this gap with real items."),
 ("h3", "4.2.9", "Confidence and the Unknown option"),
 ("p", "With the threshold of 0.59, 32 of the 3,308 test images (1.0%) were marked Unknown. The remaining 99.0% were answered with 99.1% accuracy, compared with 98.73% when every image is answered."),
 ("h3", "4.2.10", "Comparison of all versions"),
 ("tbl", "Comparison of all model versions", ["Version", "Model", "Task and data", "Test images", "Result"],
  [["V1", "Random Forest, 149 features", "TrashNet, 6 classes", "506", "73.1%"], ["V1", "Random Forest / SVM", "Garbage-10, 10 classes", "1,200", "64.7% / 57.1%"],
   ["V2", "MobileNetV2, fine-tuned", "Garbage-10, 10 classes", "1,200", "95.7%"], ["V2", "MobileNetV2, fine-tuned", "RealWaste, 10 classes", "690", "45.1% (4 categories: 75.5%)"],
   ["V3", "ConvNeXt-Tiny", "Multi-source, 10 classes", "none", "93.0% validation, epoch 2 of 15, stopped"], ["V4", "SigLIP 2 + linear classifier", "Multi-source, 4 categories", "3,308", "98.73% (macro-F1 0.9875)"],
   ["V4", "SigLIP 2 + linear classifier", "RealWaste, 4 categories", "690", "96.7%"]],
  [800, 2300, 2100, 1000, 2110], ["c", "l", "l", "r", "l"]),
 ("p", "The rows use different class sets and test sets, so only rows that share a test set can be compared directly: on RealWaste, 45.1% (ten classes) or 75.5% (four categories) for Version 2 "
       "against 96.7% for Version 4."),
 ("h3", "4.2.11", "Efficiency"),
 ("p", "After warm-up the server returned a classification in 20 to 30 ms per image on the Apple GPU (about 21 ms in the main measurement); the first request takes about half a second while the "
       "model loads. The model file is 1.5 GB (about 375 million parameters including the text encoder, of which only the image encoder runs for each frame). Computing embeddings for all 21,445 images took about "
       "five minutes in the final run, and fitting the logistic-regression classifier took a few minutes, which makes retraining with new photographs practical."),

 ("h2", "4.3", "TESTING RESULTS", "Testing Results"),
 ("h3", "4.3.1", "Automated unit tests"),
 ("p", "The project has 38 automated tests, all passing (Table 4.9). They run in a few seconds and protect the data preparation, features, models and classifier against regressions."),
 ("tbl", "Automated test suite", ["Test module", "Tests", "What is checked"],
  [["test_segmentation", "7", "Otsu mask, opening, largest component, size filter, bounding boxes on synthetic images"],
   ["test_features", "4", "149-value feature vector is finite, deterministic and sensible for a rectangle"],
   ["test_data", "4", "Dataset counts, class merging, reproducible sampling, unknown dataset error"],
   ["test_cnn", "12", "Output shapes for five architectures, transforms, checkpoint round-trip, legacy checkpoint, probabilities"],
   ["test_manifest", "5", "No duplicate files, no near-duplicate group across splits, every class in every split, split proportions"],
   ["test_waste4", "6", "Category mapping, probabilities sum to one, blend weights, save and load"],
   ["Total", "38", "All passing"]],
  [2300, 900, 5110], ["l", "c", "l"]),
 ("h3", "4.3.2", "Web server tests"),
 ("tbl", "Web server test cases", ["Test", "Expected", "Observed", "Result"],
  [["GET /api/info", "Engine name, threshold and categories", "Returned the model name and threshold", "Pass"],
   ["POST /api/classify with a plastic-bottle photograph", "JSON with a category and confidence", "Recyclable, 99.2%", "Pass"],
   ["GET / (home page)", "HTTP 200 with the page", "200, 19,584 bytes", "Pass"],
   ["GET /../../README.md (path traversal)", "Refused", "404 not found", "Pass"],
   ["POST /api/teach?category=bad", "Rejected with an error", "Error: category must be one of the four names", "Pass"]],
  [2800, 2000, 2400, 1110], ["l", "l", "l", "c"]),
 ("h3", "4.3.3", "Spot checks on sample images"),
 ("p", "Table 4.11 shows single-image checks through the web interface. They are illustrations, not an evaluation: some images come from the dataset and may have been used for training. "
       "The coconut-husk photograph is not from any training dataset."),
 ("tbl", "Spot checks on sample images", ["Image", "Predicted category", "Confidence", "Looks like"],
  [["Coconut husks (not in any dataset)", "Biodegradable", "95.5%", "a coconut shell"], ["Plastic bottle (TrashNet)", "Recyclable", "99.2%", "an empty plastic water bottle"],
   ["Food organics (RealWaste)", "Biodegradable", "99.1%", "a rotten fruit"], ["Textile (RealWaste)", "Non-recyclable", "97.9%", "a piece of cloth"],
   ["Syringe (Wikimedia)", "Medical waste", "100%", "a medicine bottle"], ["Paper (RealWaste)", "Recyclable", "91.1%", "a sheet of paper"]],
  [2800, 1900, 1300, 2310], ["l", "l", "r", "l"]),
 ("note", "[Insert here a screenshot of the web application classifying an item with the live camera, then the caption below. Replace this paragraph.]"),
 ("figcap", "Screenshot of the EcoSort AI web application (to be inserted)"),
 ("p", "**Not yet done.** Accuracy on live webcam frames has not been measured. A locked set of 200 to 300 photographs from the team's own camera is the next evaluation (Section 5.2)."),

 ("h2", "4.4", "OBSERVED RESULTS", "Observed Results"),
 ("ol", ["The final model reaches 98.73% accuracy and 0.9875 macro-F1 on 3,308 unseen images, with a training-to-test gap of 0.87 points.",
         "On real landfill photographs it reaches 96.7%, against 75.5% for the earlier CNN on the same images and the same four categories (the final model was also trained on landfill photographs).",
         "Accuracy on clean photographs did not predict real-world accuracy: MobileNetV2 scored 95.7% on its own test set and 45.1% on landfill photographs (ten classes).",
         "No ordinary item (0 of 2,998) was sent to the medical bin, and 97.7% of medical items were found.",
         "Non-recyclable items predicted as recyclable are the largest error group (22 of 42 errors).",
         "The confidence threshold of 0.59 defers 1.0% of images and raises accuracy on the answered images to 99.1%.",
         "The trained classifier alone (98.73%) clearly beats the zero-shot text method (83.3%); blending them gave no meaningful gain.",
         "Most TrashNet images (2,358 of 2,527) were duplicates of Garbage Classification images, so results on those two datasets are not independent."]),

 ("h2", "4.5", "DISCUSSION", "Discussion"),
 ("p", "**Why the earlier models failed.** The classical pipeline depends on a clean segmentation, which fails on clutter. The fine-tuned CNN learned the style of its training photographs. "
       "Both results are explained by the same cause: the training data did not look like real conditions. The decisive step was to measure on real photographs early, before trusting the 95.7% headline number."),
 ("p", "**Why SigLIP 2 works better here.** Its encoder was trained on very large collections of web images with text, so its features describe objects robustly across photo styles. Keeping it frozen and "
       "training only a small classifier on 14,847 images avoids over-fitting and keeps retraining fast. The result, 96.7% on landfill photographs, is consistent with this choice, but it must be read with one caveat: Version 4 was also trained on RealWaste training photographs "
       "(3,328 images) that Version 2 never saw, so the 21.2-point gain combines a stronger backbone with in-domain training data, and the two effects were not separated. "
       "Training MobileNetV2 on the same multi-source data would isolate them and is listed as future work."),
 ("p", "**The role of zero-shot text.** The text branch was expected to recognise medical items without training photographs. In practice the trained classifier on 1,031 medical photographs was far more accurate, so "
       "it makes the decision. The text branch remains useful for explanations and as a baseline."),
 ("p", "**Threats to validity.** (1) The medical photographs are web images and are cleaner than real hospital waste. (2) Some labels are noisy. (3) Blister packs have only 13 test photographs and TrashNet only "
       "26. (4) Different random splits changed baseline results by one to two points. (5) All results are on photograph datasets; live-camera accuracy is untested. (6) Near-duplicate detection uses a perceptual "
       "hash and may miss some copies."),
 ("p", "**Practical implications.** For a sorting station, the \"Unknown\" option and the Teach function are as important as accuracy: they let operators handle rare items and improve the model with local photographs."),
]

# =============================================================== CHAPTER 5
B += [("h1", "5", "CONCLUSION AND FUTURE ENHANCEMENT"),
 ("h2", "5.1", "CONCLUSION", "Conclusion"),
 ("p", "This project built EcoSort AI, a real-time system that sorts waste into biodegradable, recyclable, non-recyclable and medical categories, or answers Unknown when unsure. Four model "
       "generations were compared, and each change was driven by a measurement. The final model, a frozen SigLIP 2 encoder with a small trained classifier, reaches 98.73% accuracy and 0.9875 macro-F1 on 3,308 "
       "unseen images, 96.7% on real landfill photographs, 97.7% recall on medical items with no false medical alarms, and about 21 ms of model time per image."),
 ("p", "The main lesson is methodological: a model that scored 95.7% on clean photographs scored 45.1% on real landfill photographs, so evaluation on real-world data, leakage-safe splits and a validation-chosen "
       "rejection threshold are as important as the model itself. The project also delivered a reproducible pipeline, 38 automated tests and a web application with a Teach function for continuous improvement."),
 ("h2", "5.2", "FUTURE ENHANCEMENT", "Future Enhancement"),
 ("ul", ["**Live-camera evaluation.** Collect 200 to 300 photographs from the team's own camera as a locked real-world test set and report accuracy on it.",
         "**Several items per frame.** Add an object detector such as YOLO [10] and a tracker so that multiple items are found, sorted and counted.",
         "**Real medical-waste data.** Gather photographs of real items with institutional approval, and retrain with the Teach photographs.",
         "**Controlled comparison.** Train the CNN baselines on the same multi-source data, to separate the effect of the backbone from the effect of the training data.",
         "**Error analysis.** Review the 42 test errors one by one, especially non-recyclable items predicted as recyclable, and add targeted training data.",
         "**Leather and fabric items.** Add dedicated classes for leather goods, notebooks and handkerchiefs.",
         "**Edge deployment.** Export the model (ONNX or Core ML) for phones and small devices, and connect it to a bin-sorting mechanism.",
         "**Calibration.** Apply temperature scaling to the classifier so that confidence values better match accuracy."]),
]

REFERENCES = [
 "M. Tschannen et al., \"SigLIP 2: Multilingual vision-language encoders with improved semantic understanding, localization, and dense features,\" arXiv preprint, 2025.",
 "X. Zhai, B. Mustafa, A. Kolesnikov, and L. Beyer, \"Sigmoid loss for language image pre-training,\" in Proc. IEEE/CVF Int. Conf. Computer Vision (ICCV), 2023.",
 "A. Radford et al., \"Learning transferable visual models from natural language supervision,\" in Proc. Int. Conf. Machine Learning (ICML), 2021.",
 "A. Dosovitskiy et al., \"An image is worth 16x16 words: Transformers for image recognition at scale,\" in Proc. Int. Conf. Learning Representations (ICLR), 2021.",
 "J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei-Fei, \"ImageNet: A large-scale hierarchical image database,\" in Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR), 2009.",
 "K. He, X. Zhang, S. Ren, and J. Sun, \"Deep residual learning for image recognition,\" in Proc. IEEE CVPR, 2016.",
 "M. Sandler, A. Howard, M. Zhu, A. Zhmoginov, and L.-C. Chen, \"MobileNetV2: Inverted residuals and linear bottlenecks,\" in Proc. IEEE CVPR, 2018.",
 "Z. Liu et al., \"A ConvNet for the 2020s,\" in Proc. IEEE/CVF CVPR, 2022.",
 "M. Tan and Q. V. Le, \"EfficientNet: Rethinking model scaling for convolutional neural networks,\" in Proc. ICML, 2019.",
 "J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, \"You only look once: Unified, real-time object detection,\" in Proc. IEEE CVPR, 2016.",
 "S. Single, S. Iranmanesh, and R. Raad, \"RealWaste: A novel real-life data set for landfill waste classification using deep learning,\" Information, vol. 14, no. 12, 2023.",
 "M. Yang and G. Thung, \"Classification of trash for recyclability status,\" Stanford University CS229 project report, 2016.",
 "P. F. Proenca and P. Simoes, \"TACO: Trash annotations in context for litter detection,\" arXiv preprint, 2020.",
 "O. Adedeji and Z. Wang, \"Intelligent waste classification system using deep learning convolutional neural network,\" Procedia Manufacturing, vol. 35, pp. 607-612, 2019.",
 "N. Otsu, \"A threshold selection method from gray-level histograms,\" IEEE Trans. Systems, Man, and Cybernetics, vol. 9, no. 1, pp. 62-66, 1979.",
 "M.-K. Hu, \"Visual pattern recognition by moment invariants,\" IRE Trans. Information Theory, vol. 8, no. 2, pp. 179-187, 1962.",
 "T. Ojala, M. Pietikainen, and T. Maenpaa, \"Multiresolution gray-scale and rotation invariant texture classification with local binary patterns,\" IEEE Trans. Pattern Analysis and Machine Intelligence, vol. 24, no. 7, pp. 971-987, 2002.",
 "C. Cortes and V. Vapnik, \"Support-vector networks,\" Machine Learning, vol. 20, no. 3, pp. 273-297, 1995.",
 "L. Breiman, \"Random forests,\" Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.",
 "D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" in Proc. ICLR, 2015.",
 "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Machine Learning Research, vol. 12, pp. 2825-2830, 2011.",
 "A. Paszke et al., \"PyTorch: An imperative style, high-performance deep learning library,\" in Advances in Neural Information Processing Systems (NeurIPS), 2019.",
 "T. Wolf et al., \"Transformers: State-of-the-art natural language processing,\" in Proc. Conf. Empirical Methods in Natural Language Processing: System Demonstrations, 2020.",
 "\"Garbage Classification (12 classes),\" Kaggle dataset. [Online]. Available: https://www.kaggle.com/datasets/mostafaabla/garbage-classification (accessed Nov. 2026).",
 "Wikimedia Commons, freely licensed photographs of syringes, blister packs, masks, gloves, pill bottles, swabs, bandages and ampoules. [Online]. Available: https://commons.wikimedia.org (accessed Nov. 2026).",
 "United Nations, \"Transforming our world: The 2030 Agenda for Sustainable Development,\" 2015.",
 "G. Bradski, \"The OpenCV library,\" Dr. Dobb's Journal of Software Tools, 2000.",
]

CODE_FILES = [
 ("A.1", "Data preparation (scripts/prepare_data.py)", "scripts/prepare_data.py"),
 ("A.2", "SigLIP 2 wrapper and category classifier (src/waste_classifier/vlm.py)", "src/waste_classifier/vlm.py"),
 ("A.3", "Training of the final model (scripts/train_waste4.py)", "scripts/train_waste4.py"),
 ("A.4", "Inference engines (src/waste_classifier/engine.py)", "src/waste_classifier/engine.py"),
 ("A.5", "Web server (webapp/server.py)", "webapp/server.py"),
 ("A.6", "Classical segmentation (src/waste_classifier/segmentation.py)", "src/waste_classifier/segmentation.py"),
 ("A.7", "Hand-crafted features (src/waste_classifier/features.py)", "src/waste_classifier/features.py"),
]
