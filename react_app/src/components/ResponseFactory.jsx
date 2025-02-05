// react_app/src/components/ResponseFactory.jsx

import React from "react";
import TextInput from "./inputs/TextInput";
import SliderInput from "./inputs/SliderInput";
import ContinueInput from "./inputs/ContinueInput";
import NoInput from "./inputs/NoInput";
import RankingInput from "./inputs/RankingInput";
// import MultiSelectInput from "./inputs/MultiSelectInput";

const ResponseFactory = ({
  responseType,
  options,
  botMsgId,
  onSubmit
}) => {
  switch (responseType) {
    case "text":
      return <TextInput onSubmit={onSubmit} botMsgId={botMsgId}/>;
    case "continue":
      return (
        <ContinueInput
          key={botMsgId}  // Force re-render on new message
          onSubmit={onSubmit}
        />
      );
    case "slider":
      return (
        <SliderInput
          key={botMsgId}  // Force re-render on new message
          min={options?.min ?? 0}
          max={options?.max ?? 100}
          step={options?.step ?? 1}
          defaultValue={options?.default_value ?? null}
          labels={options?.labels ?? ["Not at all", "Slightly", "Moderately", "Very much", "Extremely"]}
          questionId={options?.question_id ?? "unknown_field"}
          onSubmit={onSubmit}
        />
      );
    case "ranking":
      return (
        <RankingInput
          key={botMsgId}  // Force re-render on new message
          items={options?.items ?? []}
          questionId={options?.question_id ?? "unknown_field"}
          onSubmit={onSubmit}
        />
      );
    case "noinput":
      return <NoInput />;
    default:
      // If responseType is not recognized, return NoInput
      return <NoInput />;
  }
};

export default ResponseFactory;