import React, { useState } from "react";
import { BiSearch } from "react-icons/bi";
import { Select, SelectItem } from "@nextui-org/react";

const tags = [
  "Caregiver",
  "Childcare",
  "Children",
  "COVID-19",
  "Debt",
  "Education",
  "Elderly",
  "Employment",
  "Family",
  "Family Violence",
  "Food",
  "Healthcare",
  "Homeless",
  "Housing",
  "Ex-offender",
  "Low Income",
  "Mental Health",
  "Palliative",
  "PWD",
  "Referral",
  "Special Needs",
  "Student Care",
  "Tech",
  "Transport",
  "Women",
  "Work",
  "Youth-at-Risk",
];

const QueryGenerator = () => {
  const [selectedTag, setSelectedTag] = useState("");

  return (
    <div
      className="
        border-[1px]
        w-full
        md:w-auto
        py-4
        rounded-full
        shadow-sm
        hover:shadow-md
        transition
        cursor-pointer
        flex
        justify-between
        items-center
        px-6
      "
    >
      <select
        value={selectedTag}
        onChange={(e) => setSelectedTag(e.target.value)}
        className="text-sm font-semibold border-none bg-transparent outline-none"
      >
        <option value="" disabled>Scheme Type</option>
        {tags.map((tag) => (
          <option key={tag} value={tag}>
            {tag}
          </option>
        ))}
      </select>
      <div className="text-sm font-semibold">For Who</div>
      <div className="text-sm font-semibold">Support Provided</div>
      <div className="text-sm font-semibold">Organisation</div>
      <div
        className="
          p-3
          bg-gradient-to-r from-blue-500 to-blue-700
          rounded-full
          text-white
        "
      >
        <BiSearch size={20} />
      </div>
    </div>
  );
};

export default QueryGenerator;
