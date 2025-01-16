####### CONSTANTS #######
# SURVEY_ANSWER_OPTIONS is a dictionary with
# survey id keys and lists containing properly formatted answer options
# (each option separated by letter-semicolon-letter) as values

SURVEY_ANSWER_OPTIONS = {
    "Q1t0zpGcvjT4Y3XzTOfUZTjV": {
        "3f610689-5a1b-4312-acdf-3cf674bfdb84": [
            "Normal speech processes",
            "Detectable speech disturbances",
            "Intelligible with repeating",
            "Speech combined with non-vocal communication",
            "Loss of useful speech",
        ],
        "e137e172-2fcd-4f93-c343-f864ba40addf": [
            "Normal",
            "Slight but definite excess of saliva in mouth; may have night time drooling",
            "Moderately excessive saliva; may have minimal drooling",
            "Marked excess of saliva with some drooling",
            "Marked drooling; requires constant tissue",
        ],
        "2ad0f5b8-23f2-4134-994e-e87f35adedf0": [
            "Normal eating habits",
            "Early eating problems; occasional choking",
            "Dietary consistency changes",
            "Needs supplemental tube feedings",
            "NPO (exclusively parenteral or enteral)",
        ],
        "990fe6fc-597e-4384-9707-a34480b9ff35": [
            "Normal",
            "Slow or sloppy; but no help needed",
            "Not all words are legible",
            "No words legible but can still grip pen",
            "Unable to grip pen",
        ],
        "42d7b79c-4792-4724-a3b7-b9b768f13a0f": [
            "Normal",
            "Somewhat slow and clumsy; but no help needed",
            "Can cut most foods; some help needed",
            "Food must be cut my someone but can feed self",
            "Needs to be fed",
        ],
        "587cf99d-33bb-450a-9671-ac184f3fc9c4": [
            "Normal",
            "Clumsy but able to perform all manipulations",
            "Some help needed with closures and fasteners",
            "Provides minimal assistance to caregiver",
            "Unable to perform any aspect of task",
        ],
        "a6e7fc0b-fc77-4b06-c01d-d9c43b7f45f7": [
            "Normal Function",
            "Independent; self-care with effort or decreased efficiency",
            "Intermittent assistance or substitute methods",
            "Needs attendant for self-care",
            "Total dependence",
        ],
        "2f8616ec-fca0-4e69-d457-79e2a5bc1585": [
            "Normal function",
            "Somewhat slow and clumsy but no help needed",
            "Can turn alone; or adjust sheets; with great difficulty; no  help needed",
            "Can initiate but not turn or adjust sheets alone",
            "Helpless",
        ],
        "7206fbe8-52dd-409a-d135-1162eabc9f74": [
            "Normal",
            "Early ambulation difficulties",
            "Walks with assistance including AFO; cane walker; caregiver",
            "Non ambulatory functional movement only",
            "No purposeful leg movement",
        ],
        "8e26e6e7-3bbf-45e9-9762-6cdfda335f05": [
            "Normal",
            "Slow",
            "Mild unsteadiness or fatigue; but does not need assistance",
            "Needs assistance",
            "Cannot do",
        ],
        "88c4d271-40f7-4fb5-fb2a-15bf601c0956": [
            "None",
            "Occurs when walking",
            "Occurs with one or more of the following: eating; bathing; dressing",
            "Occurs at rest either sitting or lying",
            "Significant difficulty; considering mechanical support",
        ],
        # Same question ID has different formatting based on the year of the survey
        "18889087-d590-49e4-95af-8a1ef46df742": [
            [
                "None",
                "3 Some difficulty sleeping due to shortness of breath; does not routinely use more than two pillows",
                "Needs extra pillows to sleep (+2)",
                "Can only sleep sitting up",
                "Unable to sleep without mechanical assistance",
            ],
            [
                "None",
                "Some difficulty sleeping due to shortness of breath; does not routinely use more than two pillows",
                "Needs extra pillows to sleep (+2)",
                "Can only sleep sitting up",
                "Unable to sleep without mechanical assistance",
            ],
        ],
        "33b3f3a1-814e-4403-b2cd-cd380e7df299": [
            "None",
            "Intermittent use of BiPAP",
            "Continuous use of BiPAP during the night",
            "Continuous use of BiPAP during day and night",
            "Invasive mechanical ventilation by intubation or  tracheostomy",
        ],
    }
}
SURVEY_ANSWER_OPTIONS["571e60841206f7280a92d039"] = SURVEY_ANSWER_OPTIONS[
    "Q1t0zpGcvjT4Y3XzTOfUZTjV"
]
